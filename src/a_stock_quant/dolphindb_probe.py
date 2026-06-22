"""DolphinDB 真实环境只读探测命令。

运行目标：
1. 验证本机能否连接 DolphinDB；
2. 对指定 DFS 表执行少量只读抽样；
3. 输出字段、行数和少量样例；
4. 不创建、不删除、不修改任何数据库或表。
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from collections.abc import Callable, Sequence
from typing import Any

from .data_contracts import DataContractError
from .dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)


PasswordProvider = Callable[[str], str]
AdapterFactory = Callable[
    [DolphinDBConnectionSettings],
    DolphinDBDataSourceAdapter,
]


def build_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        description="DolphinDB真实环境只读健康检查和抽样读取。"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("DOLPHINDB_HOST", "127.0.0.1"),
        help="DolphinDB主机地址，默认读取DOLPHINDB_HOST。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("DOLPHINDB_PORT", "8848")),
        help="DolphinDB端口，默认8848。",
    )
    parser.add_argument(
        "--username",
        default=os.getenv("DOLPHINDB_USERNAME", "admin"),
        help="DolphinDB用户名，默认读取DOLPHINDB_USERNAME。",
    )
    parser.add_argument(
        "--database-uri",
        default="dfs://A_STOCK_DAILY_K_DB",
        help="DFS数据库URI。",
    )
    parser.add_argument(
        "--table",
        default="stock_daily_k",
        help="只读抽样的DolphinDB表名。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="读取行数，默认5，最大1000。",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=3,
        help="终端展示的样例行数，默认3，最大20。",
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="只执行健康检查，不读取表。",
    )
    return parser


def resolve_password(
    password_provider: PasswordProvider = getpass.getpass,
) -> str:
    """优先读取环境变量，否则安全提示输入密码。"""

    password = os.getenv("DOLPHINDB_PASSWORD")

    if password is None:
        password = password_provider("请输入 DolphinDB 密码：")

    if not password:
        raise DataContractError("DolphinDB密码不能为空。")

    return password


def _default_adapter_factory(
    settings: DolphinDBConnectionSettings,
) -> DolphinDBDataSourceAdapter:
    """创建真实只读适配器。"""

    return DolphinDBDataSourceAdapter(settings=settings)


def _print_json(value: Any) -> None:
    """以可读JSON格式输出，兼容日期和第三方数值类型。"""

    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def run_probe(
    args: argparse.Namespace,
    *,
    adapter_factory: AdapterFactory = _default_adapter_factory,
    password_provider: PasswordProvider = getpass.getpass,
) -> int:
    """执行健康检查和可选的只读抽样。

    返回值：
    - 0：成功；
    - 1：健康检查失败；
    - 2：参数、连接或读取发生错误。
    """

    if not 1 <= args.limit <= 1000:
        print("错误：limit 必须是 1 到 1000 之间的整数。")
        return 2

    if not 0 <= args.preview_rows <= 20:
        print("错误：preview_rows 必须是 0 到 20 之间的整数。")
        return 2

    try:
        settings = DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=resolve_password(password_provider),
        )
        adapter = adapter_factory(settings)
        health = adapter.health_check()
    except (DataContractError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    print("=== DolphinDB只读健康检查 ===")
    print(f"状态：{health.status.value}")
    print(f"说明：{health.description or '无'}")

    if health.blocks_downstream:
        print("结论：连接或执行能力异常，停止读取。")
        return 1

    if args.health_only:
        print("结论：健康检查通过，本次未读取数据表。")
        return 0

    try:
        batch = adapter.read_raw(
            args.table,
            database_uri=args.database_uri,
            limit=args.limit,
        )
    except DataContractError as exc:
        print(f"错误：{exc}")
        return 2

    print()
    print("=== 只读抽样结果 ===")
    print(f"来源：{batch.source_location}")
    print(f"批次ID：{batch.batch_id}")
    print(f"读取行数：{batch.row_count}")
    print(f"原始字段数：{len(batch.raw_fields)}")
    print("原始字段：")
    _print_json(batch.raw_fields)

    preview_count = min(args.preview_rows, batch.row_count)

    if preview_count > 0:
        print(f"前{preview_count}行样例：")
        _print_json(batch.records[:preview_count])
    else:
        print("样例：本次没有展示数据行。")

    print()
    print("注意：本次只读抽样未推断复权方式、单位或日期语义。")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口。"""

    parser = build_parser()
    args = parser.parse_args(argv)
    return run_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
