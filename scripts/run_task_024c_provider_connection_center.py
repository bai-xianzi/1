# 本文件核心功能：离线生成“官方数据源与券商接入中心”的安全Provider卡片和动态表单示例。
# - 输入：Provider接入目录JSON、可选环境状态JSON和输出报告路径。
# - 处理：加载官方定义，生成不含任何用户凭据的UI ViewModel，并以UTF-8写入JSON。
# - 输出：Provider卡片数量、待官方字段映射数量和报告位置；不联网、不导入券商SDK、不读取秘密。
# - 常量依据：领域逻辑来自`provider_connection_center.py`，目录来自TASK_024A/024B的官方来源清单。
# - 为什么这样写：先用离线CLI验收前后端共享合同，之后再接桌面或Web UI，避免一开始绑定未知前端框架。
"""Generate the TASK_024C connection-center UI contract report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.provider_connection_center import (
    build_connection_center_view,
    load_connection_catalog,
)


# 本段代码核心功能：创建命令行参数解析器。
# - 输入：无外部输入，使用固定参数定义。
# - 处理：声明目录、环境状态和输出路径。
# - 输出：ArgumentParser对象。
# - 常量依据：默认路径与项目目录结构一致，全部操作为离线只读或本地报告写入。
# - 为什么这样写：显式参数便于PowerShell验证脚本和未来CI复用。
def build_parser() -> argparse.ArgumentParser:
    """Build the TASK_024C CLI parser."""

    parser = argparse.ArgumentParser(
        description="Generate the provider connection-center UI contract."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path(
            "configs/providers/provider_connection_center_catalog_v1.json"
        ),
    )
    parser.add_argument("--environment-status", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


# 本段代码核心功能：读取可选的安全环境状态映射。
# - 输入：可为空的UTF-8 JSON路径。
# - 处理：无路径时返回空映射；有路径时只接受字符串键值对象。
# - 输出：provider_id到状态字符串的字典。
# - 常量依据：环境状态只用于UI提示，不参与秘密处理或自动激活。
# - 为什么这样写：把TASK_024B后台发现结果接入UI，但不让它成为唯一用户入口。
def load_environment_status(path: Path | None) -> dict[str, str]:
    """Load an optional provider environment-status mapping."""

    # 本段代码核心功能：处理未提供环境报告的正常情况。
    # - 输入：path是否为None。
    # - 处理：直接返回空字典。
    # - 输出：空映射。
    # - 常量依据：UI接入中心可在未运行24B扫描时正常展示。
    # - 为什么这样写：后台扫描是增强提示，不是启动UI的硬依赖。
    if path is None:
        return {}

    raw = json.loads(path.read_text(encoding="utf-8-sig"))

    # 本段代码核心功能：校验环境状态JSON为对象。
    # - 输入：解析后的raw。
    # - 处理：类型检查。
    # - 输出：非法时抛出ValueError。
    # - 常量依据：键值映射比完整机器报告更适合最小权限输入。
    # - 为什么这样写：避免CLI意外回写或暴露整机软件清单。
    if not isinstance(raw, dict):
        raise ValueError("environment status must be an object")

    result: dict[str, str] = {}

    # 本段代码核心功能：逐项规范化Provider环境状态。
    # - 输入：raw键值对。
    # - 处理：要求键值均为非空字符串。
    # - 输出：更新result。
    # - 常量依据：ViewModel只需要简短状态码。
    # - 为什么这样写：严格输入防止复杂对象进入UI报告。
    for key, value in raw.items():
        # 本段代码核心功能：拒绝非法环境状态条目。
        # - 输入：当前键值。
        # - 处理：字符串与非空检查。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：Provider标识与状态码都是字符串。
        # - 为什么这样写：避免静默字符串化敏感对象。
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("environment status keys and values must be strings")
        # 本段代码核心功能：根据条件 `not key.strip() or not value.strip()` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not key.strip() or not value.strip():
            raise ValueError("environment status keys and values cannot be empty")
        result[key.strip()] = value.strip()

    return result


# 本段代码核心功能：执行离线ViewModel生成流程。
# - 输入：命令行参数。
# - 处理：加载目录和可选状态、生成卡片、统计待官方映射项并写UTF-8 JSON。
# - 输出：进程返回码0和控制台摘要。
# - 常量依据：本任务禁止网络、SDK导入、凭据读取和Provider激活。
# - 为什么这样写：让Windows本地能在真正UI开发前验证所有安全合同。
def main() -> int:
    """Run the TASK_024C offline contract generator."""

    args = build_parser().parse_args()
    definitions = load_connection_catalog(args.catalog)
    environment_status = load_environment_status(args.environment_status)
    cards = build_connection_center_view(
        definitions,
        environment_status=environment_status,
    )
    pending_official_fields = sum(
        1
        for card in cards
        if card["form_definition_status"] != "OFFICIAL_FIELDS_VERIFIED"
    )
    report = {
        "task_id": "TASK_024C",
        "mode": "OFFLINE_PROVIDER_CONNECTION_CENTER_CONTRACT",
        "overall_status": "PASSED",
        "provider_card_count": len(cards),
        "pending_official_field_mapping_count": pending_official_fields,
        "secret_values_recorded": 0,
        "network_calls": 0,
        "provider_sdk_imports": 0,
        "execution_activation": "BLOCKED",
        "next_task": "TASK_024D_WINDOWS_CREDENTIAL_REFERENCE_BACKEND",
        "provider_cards": cards,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Provider cards: {len(cards)}")
    print(f"Pending official field mappings: {pending_official_fields}")
    print("Secret values recorded: 0")
    print("Execution activation: BLOCKED")
    print(f"Report: {args.output}")
    return 0


# 本段代码核心功能：仅在脚本直接运行时启动CLI。
# - 输入：Python模块运行上下文。
# - 处理：检查`__name__`并把main返回码交给SystemExit。
# - 输出：标准进程退出码。
# - 常量依据：导入该脚本进行测试时不得自动执行文件写入。
# - 为什么这样写：保持入口可测试且无导入副作用。
if __name__ == "__main__":
    raise SystemExit(main())
