"""验证TASK_017B字段字典升级和七类Canonical合同。"""
# 本脚本核心功能：验证任务017b字典升级的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

import yaml

from a_stock_quant.daily_funds_canonical_contract import validate_contract
from a_stock_quant.field_dictionary_governance import validate_dictionary_governance


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    # 输出结果：返回 `parser` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return parser


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：argv。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    canonical_path = root / "schemas" / "canonical_fields.yaml"
    canonical = yaml.safe_load(canonical_path.read_text(encoding="utf-8"))
    lifecycle = Counter(
        field["lifecycle_stage"]
        for domain in canonical["domains"]
        for field in domain["fields"]
    )
    governance = validate_dictionary_governance(root)
    mapping = validate_contract(
        root / "configs" / "mappings" / "a_stock_daily_funds_canonical_v0.yaml",
        canonical_path,
    )
    errors = []
    # 条件分支：检查 `governance['overall_status'] != 'PASSED'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if governance["overall_status"] != "PASSED":
        errors.append({"component":"field_governance","issues":governance["issues"]})
    # 条件分支：检查 `mapping['overall_status'] != 'PASSED_WITH_WARNINGS'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if mapping["overall_status"] != "PASSED_WITH_WARNINGS":
        errors.append({"component":"canonical_contract","issues":mapping["issues"]})
    expected = {
        "dictionary_revision":"0.6.0",
        "domain_count":46,
        "field_count":1235,
        "core_count":744,
        "near_term_count":50,
        "future_reserved_count":441,
    }
    actual = {
        "dictionary_revision":str(canonical.get("dictionary_revision")),
        "domain_count":len(canonical.get("domains", [])),
        "field_count":sum(lifecycle.values()),
        "core_count":lifecycle.get("core", 0),
        "near_term_count":lifecycle.get("near_term", 0),
        "future_reserved_count":lifecycle.get("future_reserved", 0),
    }
    # 条件分支：检查 `actual != expected` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if actual != expected:
        errors.append({"component":"dictionary_counts","expected":expected,"actual":actual})
    result = {
        "task_id":"TASK_017B",
        **actual,
        "mapping_dataset_count":mapping["dataset_count"],
        "ready_with_warning_count":mapping["ready_with_warning_count"],
        "blocked_count":mapping["blocked_count"],
        "overall_status":"PASSED_WITH_WARNINGS" if not errors else "FAILED",
        "issues":errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # 输出结果：返回 `0 if not errors else 1` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if not errors else 1


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
