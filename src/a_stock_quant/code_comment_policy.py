# 本模块核心功能：加载并校验项目教学式代码注释政策，为审计脚本和单元测试提供稳定的数据合同。
# - json负责读取机器可读政策文件，读取后把JSON对象转换成Python字典和不可变数据类。
# - dataclass用于定义强类型政策对象，防止审计器直接依赖松散字典键名。
# - Enum表示迁移状态等有限值，避免大小写或拼写差异造成门禁失效。
# - Path统一处理Windows和其他平台路径，输入可以是字符串或Path对象。
# - 为什么这样写：注释规则本身也必须可测试、可版本化和可审计，不能只存在于Markdown自然语言中。
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .data_contracts import DataContractError


# 迁移状态枚举：限定全仓库注释迁移只能处于进行中、完成或阻断三种状态。
# - IN_PROGRESS表示历史代码仍在分批补注释，此时全仓库强制审计尚未开启。
# - COMPLETE表示全部目标文件已经通过强制审计，可以进入用户确认门禁。
# - BLOCKED表示政策或审计数据异常，所有提交动作必须停止。
# - 为什么这样写：有限状态机比自由文本可靠，能够防止把“差不多完成”误判为正式完成。
class CommentMigrationStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"


# 文本字段校验：确保政策中的关键标识不是空字符串。
# - value接收JSON反序列化后的任意值。
# - field_name用于生成可定位的错误消息。
# - 返回值会去除首尾空白，避免视觉相同但实际不同的标识。
# - 为什么这样写：机器门禁依赖精确字符串，空值或隐藏空格会使规则静默失效。
def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


# 唯一文本列表校验：把JSON数组转换为不可变元组，并拒绝空值或重复项。
# - values通常对应扩展名、必需结构、例外目录或禁止模式。
# - allow_empty控制某个列表是否允许为空；权威规则列表默认不允许为空。
# - 返回tuple可以避免加载后被调用方意外修改。
# - 为什么这样写：重复规则会让审计统计失真，运行期修改政策则会破坏可重复性。
def _unique_texts(
    values: Iterable[Any],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    result = tuple(
        _require_text(value, field_name)
        for value in values
    )
    if not allow_empty and not result:
        raise DataContractError(f"{field_name}不能为空。")
    if len(result) != len(set(result)):
        raise DataContractError(f"{field_name}不允许重复。")
    return result


# Git门禁数据合同：集中保存提交和推送前必须执行的检查以及用户确认要求。
# - 所有字段都是布尔值，True表示该门禁必须执行。
# - user_confirmation_required_before_commit和push分别控制本地提交与远程推送。
# - 为什么这样写：把用户确认从口头约定升级为机器可验证合同，防止其他代理绕过。
@dataclass(frozen=True, slots=True)
class CommentGitGate:
    must_run_comment_audit: bool
    must_run_specialized_tests: bool
    must_run_full_tests: bool
    must_run_encoding_audit: bool
    must_run_git_diff_check: bool
    user_confirmation_required_before_commit: bool
    user_confirmation_required_before_push: bool

    # Git门禁自校验：七项必须全部为True，任何False都代表政策被弱化。
    # - all读取所有布尔字段并计算逻辑与。
    # - 失败时抛出DataContractError，阻止政策加载和后续任务执行。
    # - 为什么这样写：本项目要求100%遵守，不能允许某个配置项被临时关闭。
    def __post_init__(self) -> None:
        if not all(
            (
                self.must_run_comment_audit,
                self.must_run_specialized_tests,
                self.must_run_full_tests,
                self.must_run_encoding_audit,
                self.must_run_git_diff_check,
                self.user_confirmation_required_before_commit,
                self.user_confirmation_required_before_push,
            )
        ):
            raise DataContractError(
                "代码注释Git门禁的全部开关必须为true。"
            )


# 迁移政策数据合同：描述当前全仓库迁移阶段和提交阻断状态。
# - batch_count是规划批次数，必须大于0。
# - full_repository_enforcement_enabled只有全部迁移完成后才能为True。
# - new_or_modified_code_enforcement_enabled要求新代码从政策启用当天起立即合规。
# - 为什么这样写：历史债务可以分批处理，但新债务必须立即停止增长。
@dataclass(frozen=True, slots=True)
class CommentMigrationPolicy:
    status: CommentMigrationStatus
    inventory_report: str
    batch_count: int
    full_repository_enforcement_enabled: bool
    new_or_modified_code_enforcement_enabled: bool
    github_commit_blocked_until_full_migration: bool
    github_push_blocked_until_user_confirmation: bool

    # 迁移状态校验：确保进行中状态保持提交阻断，并开启新增代码审计。
    # - batch_count必须是正整数，布尔值不能冒充整数。
    # - IN_PROGRESS时全仓库强制模式必须关闭，否则历史文件会让所有工具无法运行。
    # - COMPLETE时全仓库强制模式必须开启，避免迁移完成后仍处于宽松模式。
    # - 为什么这样写：分阶段迁移需要明确的状态转换，不能靠人工记忆切换审计强度。
    def __post_init__(self) -> None:
        if (
            isinstance(self.batch_count, bool)
            or not isinstance(self.batch_count, int)
            or self.batch_count < 1
        ):
            raise DataContractError("batch_count必须是正整数。")
        object.__setattr__(
            self,
            "inventory_report",
            _require_text(
                self.inventory_report,
                "inventory_report",
            ),
        )
        if not self.new_or_modified_code_enforcement_enabled:
            raise DataContractError(
                "新增或修改代码必须立即开启注释审计。"
            )
        if not self.github_push_blocked_until_user_confirmation:
            raise DataContractError(
                "GitHub推送必须等待用户确认。"
            )
        if self.status is CommentMigrationStatus.IN_PROGRESS:
            if self.full_repository_enforcement_enabled:
                raise DataContractError(
                    "迁移进行中不得提前开启全仓库强制模式。"
                )
            if not self.github_commit_blocked_until_full_migration:
                raise DataContractError(
                    "迁移进行中必须阻断Git提交。"
                )
        if self.status is CommentMigrationStatus.COMPLETE:
            if not self.full_repository_enforcement_enabled:
                raise DataContractError(
                    "迁移完成后必须开启全仓库强制模式。"
                )


# 顶层政策数据合同：保存权威文件、适用结构、例外和Git门禁。
# - required_comment_structure定义每个教学式注释块必须覆盖的语义。
# - forbidden_patterns定义审计和人工评审必须拒绝的写法。
# - migration和git_gate组合形成当前阶段的完整执行边界。
# - 为什么这样写：单一对象让脚本、测试和后续代理读取同一权威来源，避免多套规则分叉。
@dataclass(frozen=True, slots=True)
class CodeCommentPolicy:
    task_id: str
    policy_version: str
    policy_status: str
    authority_document: str
    principle: str
    required_comment_structure: tuple[str, ...]
    exceptions: tuple[str, ...]
    forbidden_patterns: tuple[str, ...]
    migration: CommentMigrationPolicy
    git_gate: CommentGitGate

    # 顶层政策自校验：锁定任务标识、原则和必需结构数量。
    # - task_id必须等于TASK_021A，防止误加载其他工程政策。
    # - principle必须保持教学式前置注释原则。
    # - required_comment_structure至少包含七项，覆盖概括、细节、变化、常量、原因、实例和顺序。
    # - 为什么这样写：这些字段是用户六条规则的机器化映射，缺少任何一项都会降低约束。
    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "policy_version",
            "policy_status",
            "authority_document",
            "principle",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        if self.task_id != "TASK_021A":
            raise DataContractError("代码注释政策task_id异常。")
        if (
            self.principle
            != "TEACHING_STYLE_PRECEDING_COMMENTS_REQUIRED"
        ):
            raise DataContractError("代码注释政策原则异常。")
        object.__setattr__(
            self,
            "required_comment_structure",
            _unique_texts(
                self.required_comment_structure,
                "required_comment_structure",
            ),
        )
        object.__setattr__(
            self,
            "exceptions",
            _unique_texts(
                self.exceptions,
                "exceptions",
            ),
        )
        object.__setattr__(
            self,
            "forbidden_patterns",
            _unique_texts(
                self.forbidden_patterns,
                "forbidden_patterns",
            ),
        )
        if len(self.required_comment_structure) < 7:
            raise DataContractError(
                "教学式注释必需结构不得少于七项。"
            )


# 政策加载器：从UTF-8 JSON文件构造并校验不可变CodeCommentPolicy。
# - path可以是字符串或Path，读取后要求根节点为对象。
# - migration和git_gate分别转换成嵌套数据类。
# - JSON中的额外语言细节由审计脚本直接读取，核心门禁由本数据合同验证。
# - 为什么这样写：加载即校验可以让错误政策在任务开始时失败，而不是到Git提交时才暴露。
def load_code_comment_policy(
    path: str | Path,
) -> CodeCommentPolicy:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise DataContractError("代码注释政策根节点必须是对象。")

    migration_raw = raw["migration"]
    gate_raw = raw["git_gate"]

    migration = CommentMigrationPolicy(
        status=CommentMigrationStatus(
            str(migration_raw["status"])
        ),
        inventory_report=str(
            migration_raw["inventory_report"]
        ),
        batch_count=int(migration_raw["batch_count"]),
        full_repository_enforcement_enabled=bool(
            migration_raw[
                "full_repository_enforcement_enabled"
            ]
        ),
        new_or_modified_code_enforcement_enabled=bool(
            migration_raw[
                "new_or_modified_code_enforcement_enabled"
            ]
        ),
        github_commit_blocked_until_full_migration=bool(
            migration_raw[
                "github_commit_blocked_until_full_migration"
            ]
        ),
        github_push_blocked_until_user_confirmation=bool(
            migration_raw[
                "github_push_blocked_until_user_confirmation"
            ]
        ),
    )

    gate = CommentGitGate(
        must_run_comment_audit=bool(
            gate_raw["must_run_comment_audit"]
        ),
        must_run_specialized_tests=bool(
            gate_raw["must_run_specialized_tests"]
        ),
        must_run_full_tests=bool(
            gate_raw["must_run_full_tests"]
        ),
        must_run_encoding_audit=bool(
            gate_raw["must_run_encoding_audit"]
        ),
        must_run_git_diff_check=bool(
            gate_raw["must_run_git_diff_check"]
        ),
        user_confirmation_required_before_commit=bool(
            gate_raw[
                "user_confirmation_required_before_commit"
            ]
        ),
        user_confirmation_required_before_push=bool(
            gate_raw[
                "user_confirmation_required_before_push"
            ]
        ),
    )

    return CodeCommentPolicy(
        task_id=str(raw["task_id"]),
        policy_version=str(raw["policy_version"]),
        policy_status=str(raw["policy_status"]),
        authority_document=str(raw["authority_document"]),
        principle=str(raw["principle"]),
        required_comment_structure=tuple(
            str(value)
            for value in raw["required_comment_structure"]
        ),
        exceptions=tuple(
            str(value) for value in raw["exceptions"]
        ),
        forbidden_patterns=tuple(
            str(value)
            for value in raw["forbidden_patterns"]
        ),
        migration=migration,
        git_gate=gate,
    )
