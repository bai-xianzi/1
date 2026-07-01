# 本脚本核心功能：验证任务015来源模板的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import json
from pathlib import Path

from a_stock_quant.source_governance import (
    DatasetSourceBinding,
    SourceCapability,
    SourceDescriptor,
    SourceRole,
)


# 配置常量：集中定义 `ROOT`，供后续流程复用。
# - 当前值或构造表达式：`Path(__file__).resolve().parents[1]`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
ROOT = Path(__file__).resolve().parents[1]


# 函数 `load_json`：完成加载JSON相关处理。
# - 输入：path。
# - 处理：完成加载JSON相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def load_json(path: Path) -> dict:
    # 输出结果：返回 `json.loads(path.read_text(encoding='utf-8'))` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return json.loads(path.read_text(encoding="utf-8"))


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    source_dir = ROOT / "configs" / "sources"
    sources = [
        SourceDescriptor.from_dict(
            load_json(path)
        )
        for path in sorted(source_dir.glob("*.json"))
    ]

    assert sources
    assert all(not item.enabled for item in sources)

    binding_payload = load_json(
        ROOT
        / "configs"
        / "source_bindings"
        / "a_stock_daily_bar.multi_source.template.json"
    )
    bindings = []
    # 循环处理：将 `binding_payload['bindings']` 中的元素逐项绑定到 `payload`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for payload in binding_payload["bindings"]:
        bindings.append(
            DatasetSourceBinding(
                dataset_id=binding_payload["dataset_id"],
                source_id=payload["source_id"],
                role=SourceRole(payload["role"]),
                priority=payload["priority"],
                source_locator=payload["source_locator"],
                mapping_version=payload["mapping_version"],
                source_schema_version=payload[
                    "source_schema_version"
                ],
                required_capabilities=tuple(
                    SourceCapability(item)
                    for item in payload.get(
                        "required_capabilities",
                        [],
                    )
                ),
                enabled=payload["enabled"],
                notes=payload.get("notes", ""),
            )
        )

    assert len(bindings) == 3
    assert bindings[0].role is SourceRole.PRIMARY

    inventory = load_json(
        ROOT
        / "configs"
        / "inventory"
        / "seven_snapshot_inventory.template.json"
    )
    assert [
        item["dataset_id"]
        for item in inventory["datasets"]
    ] == [
        "hq",
        "hy",
        "gn",
        "kphq",
        "kphy",
        "kpgn",
        "zj",
    ]

    forbidden = (
        "D:\\Users\\Administrator",
        "C:\\Users\\Administrator",
    )
    # 循环处理：将 `ROOT.rglob('*')` 中的元素逐项绑定到 `path`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for path in ROOT.rglob("*"):
        # 条件分支：检查 `not path.is_file()` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not path.is_file():
            continue
        # 条件分支：检查 `path.suffix.lower() not in {'.py', '.json', '.md'}` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if path.suffix.lower() not in {
            ".py",
            ".json",
            ".md",
        }:
            continue
        text = path.read_text(
            encoding="utf-8"
        )
        # 循环处理：将 `forbidden` 中的元素逐项绑定到 `marker`。
        # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
        # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
        for marker in forbidden:
            assert marker not in text, (
                f"发现本机路径：{path}"
            )

    print(
        "TASK_015 source templates validation PASSED."
    )
    # 输出结果：返回 `0` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
