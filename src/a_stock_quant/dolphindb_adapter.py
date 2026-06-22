"""DolphinDB 只读数据源适配器。

当前版本只负责：
1. 建立只读连接；
2. 执行健康检查；
3. 按限制行数读取原始表；
4. 执行项目内部生成的安全只读查询；
5. 转换为 RawDataBatch。

本模块不会创建、删除或修改 DolphinDB 数据库和表。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .data_contracts import (
    DataContractError,
    DataQualityResult,
    DataSourceAdapter,
    QualityLevel,
    QualityStatus,
    RawDataBatch,
    SourceType,
)


class DolphinDBSessionProtocol(Protocol):
    """DolphinDB 会话需要提供的最小方法。"""

    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> Any:
        """连接 DolphinDB。"""

    def run(self, script: str) -> Any:
        """运行 DolphinDB 脚本并返回结果。"""


SessionFactory = Callable[[], DolphinDBSessionProtocol]


@dataclass(frozen=True, slots=True)
class DolphinDBConnectionSettings:
    """DolphinDB 连接参数。"""

    host: str
    port: int
    username: str
    password: str

    def __post_init__(self) -> None:
        """检查连接参数。"""

        if not self.host.strip():
            raise DataContractError("host 不能为空。")

        if not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            raise DataContractError("port 必须是 1 到 65535 之间的整数。")

        if not self.username.strip():
            raise DataContractError("username 不能为空。")


class DolphinDBDataSourceAdapter(DataSourceAdapter):
    """DolphinDB 的最小只读适配器。"""

    _TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    _DATABASE_URI_PATTERN = re.compile(r"^dfs://[A-Za-z0-9_.-]+$")
    _READ_ONLY_PREFIX_PATTERN = re.compile(
        r"^(select|exec)\b",
        re.IGNORECASE,
    )
    _FORBIDDEN_SCRIPT_PATTERN = re.compile(
        r"\b(insert|update|delete|drop|create|alter|rename|truncate|"
        r"grant|revoke)\b|append!|upsert!|tableInsert|saveTable|"
        r"loadTextEx|dropDatabase|database\s*\(",
        re.IGNORECASE,
    )

    def __init__(
        self,
        settings: DolphinDBConnectionSettings,
        session_factory: SessionFactory | None = None,
        source_id: str = "dolphindb_primary",
    ) -> None:
        """保存连接设置，但不在初始化时立即连接。"""

        super().__init__(
            source_id=source_id,
            source_type=SourceType.DOLPHINDB,
        )
        self.settings = settings
        self._session_factory = session_factory or self._default_session_factory
        self._session: DolphinDBSessionProtocol | None = None

    @staticmethod
    def _default_session_factory() -> DolphinDBSessionProtocol:
        """创建真实 DolphinDB 会话。"""

        try:
            import dolphindb as ddb
        except ImportError as exc:
            raise DataContractError(
                "未安装 dolphindb Python 客户端，无法建立真实连接。"
            ) from exc

        return ddb.session()

    def _get_session(self) -> DolphinDBSessionProtocol:
        """按需建立并缓存会话。"""

        if self._session is None:
            session = self._session_factory()

            try:
                session.connect(
                    self.settings.host,
                    self.settings.port,
                    self.settings.username,
                    self.settings.password,
                )
            except Exception as exc:
                raise DataContractError(
                    f"DolphinDB 连接失败：{exc}"
                ) from exc

            self._session = session

        return self._session

    @classmethod
    def _validate_database_uri(cls, database_uri: str) -> None:
        """限制数据库URI格式。"""

        if not cls._DATABASE_URI_PATTERN.fullmatch(database_uri):
            raise DataContractError(
                "database_uri 必须使用 dfs://数据库名 格式。"
            )

    @classmethod
    def _validate_table_name(cls, table_name: str) -> None:
        """限制表名只能使用字母、数字和下划线。"""

        if not cls._TABLE_NAME_PATTERN.fullmatch(table_name):
            raise DataContractError(
                "source_object_name 不是合法的 DolphinDB 表名。"
            )

    @staticmethod
    def _normalise_records(result: Any) -> tuple[list[str], list[dict[str, Any]]]:
        """把常见 DolphinDB 返回值转换为字段列表和字典记录。"""

        if result is None:
            return [], []

        if isinstance(result, list):
            if any(not isinstance(item, dict) for item in result):
                raise DataContractError(
                    "DolphinDB 返回的列表中存在非字典记录。"
                )

            fields = list(result[0].keys()) if result else []
            return fields, result

        to_dict = getattr(result, "to_dict", None)
        columns = getattr(result, "columns", None)

        if callable(to_dict) and columns is not None:
            try:
                records = to_dict(orient="records")
            except TypeError:
                records = to_dict("records")

            if any(not isinstance(item, dict) for item in records):
                raise DataContractError(
                    "DolphinDB 表格结果无法转换为字典记录。"
                )

            return [str(column) for column in columns], list(records)

        raise DataContractError(
            "暂不支持当前 DolphinDB 返回值类型。"
        )

    def health_check(self) -> DataQualityResult:
        """通过执行 1 + 1 检查连接和基本执行能力。"""

        try:
            result = self._get_session().run("1 + 1")
            passed = result == 2
        except Exception as exc:
            return DataQualityResult(
                check_name="DolphinDB连接健康检查",
                level=QualityLevel.CRITICAL,
                status=QualityStatus.FAILED,
                checked_row_count=1,
                failed_row_count=1,
                blocking=True,
                description=f"健康检查执行失败：{exc}",
            )

        return DataQualityResult(
            check_name="DolphinDB连接健康检查",
            level=QualityLevel.INFO if passed else QualityLevel.CRITICAL,
            status=QualityStatus.PASSED if passed else QualityStatus.FAILED,
            checked_row_count=1,
            failed_row_count=0 if passed else 1,
            blocking=not passed,
            description=(
                "DolphinDB连接和脚本执行正常。"
                if passed
                else f"健康检查返回异常结果：{result!r}"
            ),
        )

    def run_readonly_query(self, script: str) -> Any:
        """执行经过安全检查的只读 select/exec 查询。"""

        if not isinstance(script, str) or not script.strip():
            raise DataContractError("只读查询脚本不能为空。")

        normalized = " ".join(script.split())

        if ";" in normalized:
            raise DataContractError("只读查询不允许包含分号。")

        if re.search(r"(^|\s)//", normalized) or "/*" in normalized:
            raise DataContractError("只读查询不允许包含注释。")

        if not self._READ_ONLY_PREFIX_PATTERN.match(normalized):
            raise DataContractError(
                "只读查询只能以 select 或 exec 开头。"
            )

        if self._FORBIDDEN_SCRIPT_PATTERN.search(normalized):
            raise DataContractError(
                "只读查询中包含被禁止的写入或结构变更关键字。"
            )

        try:
            return self._get_session().run(script)
        except Exception as exc:
            raise DataContractError(
                f"DolphinDB只读查询失败：{exc}"
            ) from exc

    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        """从指定 DFS 表读取有限行原始数据。"""

        database_uri = kwargs.get("database_uri")
        limit = kwargs.get("limit", 100)

        if not isinstance(database_uri, str):
            raise DataContractError(
                "read_raw 必须提供字符串 database_uri。"
            )

        if not isinstance(limit, int) or not 1 <= limit <= 100_000:
            raise DataContractError(
                "limit 必须是 1 到 100000 之间的整数。"
            )

        self._validate_database_uri(database_uri)
        self._validate_table_name(source_object_name)

        script = (
            f'select top {limit} * '
            f'from loadTable("{database_uri}", `{source_object_name})'
        )

        try:
            result = self._get_session().run(script)
        except Exception as exc:
            raise DataContractError(
                f"DolphinDB 读取失败：{exc}"
            ) from exc

        raw_fields, records = self._normalise_records(result)

        return RawDataBatch(
            source_id=self.source_id,
            source_type=self.source_type,
            source_object_name=source_object_name,
            raw_fields=raw_fields,
            records=records,
            source_location=f"{database_uri}/{source_object_name}",
            notes=(
                f"只读抽样查询，limit={limit}；"
                "未推断复权、单位或日期语义。"
            ),
        )
