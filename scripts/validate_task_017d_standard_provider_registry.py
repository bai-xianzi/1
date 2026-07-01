"""验证 TASK_017D 七类 StandardDataService Provider 注册合同。"""
# 本脚本核心功能：验证任务017d标准化Provider注册表的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import yaml

from a_stock_quant.daily_funds_canonical_contract import REQUIRED_DATASETS
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    STANDARD_QUERY_CONTRACT_VERSION,
)


# 函数 `_load`：完成加载相关处理。
# - 输入：path。
# - 处理：完成加载相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict[str, Any]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    # 条件分支：检查 `not isinstance(payload, dict)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not isinstance(payload, dict):
        # 失败门禁：抛出 `ValueError(f'YAML根节点必须是映射：{path}')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise ValueError(f"YAML根节点必须是映射：{path}")
    # 输出结果：返回 `payload` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return payload


# 函数 `validate`：完成验证相关处理。
# - 输入：project_root。
# - 处理：完成验证相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict[str, Any]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def validate(project_root: Path) -> dict[str, Any]:
    registry = _load(
        project_root
        / "configs/datasets/a_stock_daily_funds_standard_providers.yaml"
    )
    service = _load(
        project_root
        / "configs/datasets/a_stock_daily_funds_standard_service.yaml"
    )
    providers = dict(registry.get("providers", {}))
    issues: list[dict[str, Any]] = []

    # 条件分支：检查 `registry.get('standard_query_contract_version') != STANDARD_QUERY_CONTRACT_VERSION` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if registry.get("standard_query_contract_version") != STANDARD_QUERY_CONTRACT_VERSION:
        issues.append({"severity": "ERROR", "code": "QUERY_CONTRACT_VERSION_MISMATCH"})
    # 条件分支：检查 `tuple(providers) != REQUIRED_DATASETS` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if tuple(providers) != REQUIRED_DATASETS:
        issues.append({"severity": "ERROR", "code": "PROVIDER_DATASET_SET_OR_ORDER_MISMATCH"})

    provider_ids = [str(item.get("provider_id", "")) for item in providers.values()]
    # 条件分支：检查 `len(provider_ids) != len(set(provider_ids))` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(provider_ids) != len(set(provider_ids)):
        issues.append({"severity": "ERROR", "code": "PROVIDER_ID_DUPLICATE"})

    service_profiles = dict(service.get("dataset_profiles", {}))
    instrument_count = 0
    entity_count = 0
    # 循环处理：将 `providers.items()` 中的元素逐项绑定到 `(dataset_id, item)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for dataset_id, item in providers.items():
        mode = item.get("selector_mode")
        # 条件分支：检查 `mode == INSTRUMENT_SELECTOR_MODE` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if mode == INSTRUMENT_SELECTOR_MODE:
            instrument_count += 1
        # 条件分支：检查 `mode == ENTITY_SELECTOR_MODE` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        elif mode == ENTITY_SELECTOR_MODE:
            entity_count += 1
        else:
            issues.append({"severity": "ERROR", "code": "SELECTOR_MODE_INVALID", "dataset_id": dataset_id})
        profile = service_profiles.get(dataset_id, {})
        # 条件分支：检查 `item.get('canonical_object') != profile.get('canonical_object')` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if item.get("canonical_object") != profile.get("canonical_object"):
            issues.append({"severity": "ERROR", "code": "CANONICAL_OBJECT_MISMATCH", "dataset_id": dataset_id})
        raw_mode = profile.get("selector_mode")
        expected_mode = (
            INSTRUMENT_SELECTOR_MODE
            if raw_mode == "INSTRUMENT_ID"
            else ENTITY_SELECTOR_MODE
        )
        # 条件分支：检查 `mode != expected_mode` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if mode != expected_mode:
            issues.append({"severity": "ERROR", "code": "SELECTOR_SEMANTIC_MISMATCH", "dataset_id": dataset_id})

    errors = [item for item in issues if item["severity"] == "ERROR"]
    # 输出结果：返回 `{'task_id': 'TASK_017D', 'registry_version': str(registry.get('registry_version', '')),...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return {
        "task_id": "TASK_017D",
        "registry_version": str(registry.get("registry_version", "")),
        "standard_query_contract_version": STANDARD_QUERY_CONTRACT_VERSION,
        "provider_count": len(providers),
        "instrument_selector_provider_count": instrument_count,
        "entity_selector_provider_count": entity_count,
        "canonical_object_count": len({item.get("canonical_object") for item in providers.values()}),
        "overall_status": "PASSED_WITH_WARNINGS" if not errors else "FAILED",
        "issues": issues,
    }


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：argv。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args(argv)
    result = validate(Path(args.project_root).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # 输出结果：返回 `0 if result['overall_status'] == 'PASSED_WITH_WARNINGS' else 1` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if result["overall_status"] == "PASSED_WITH_WARNINGS" else 1


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
