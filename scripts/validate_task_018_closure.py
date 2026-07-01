# 本脚本核心功能：验证任务018关闭验收的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path


# 配置常量：集中定义 `EXPECTED_REAL`，供后续流程复用。
# - 当前值或构造表达式：`{'provider_count': 9, 'dataset_count': 9, 'usage_count': 4, 'assessment_count': 36, 'ev...`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
EXPECTED_REAL = {
    "provider_count": 9,
    "dataset_count": 9,
    "usage_count": 4,
    "assessment_count": 36,
    "evidence_dimension_count": 8,
    "current_research_usable_count": 9,
    "current_research_warning_count": 9,
    "manual_decision_block_count": 9,
    "strict_historical_block_count": 9,
    "historical_training_block_count": 9,
    "database_connection_attempted": True,
    "database_readonly_query_mode": True,
    "write_operation_count": 0,
}


# 函数 `require`：完成强制校验相关处理。
# - 输入：condition、message。
# - 处理：完成强制校验相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def require(condition: bool, message: str) -> None:
    # 条件分支：检查 `not condition` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not condition:
        # 失败门禁：抛出 `RuntimeError(message)`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise RuntimeError(message)


# 函数 `load_json`：完成加载JSON相关处理。
# - 输入：path。
# - 处理：完成加载JSON相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def load_json(path: Path) -> dict:
    require(path.exists(), f"缺少文件：{path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON根节点必须是对象：{path}")
    # 输出结果：返回 `value` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return value


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()

    required = [
        root / "PROJECT_STATUS.md",
        root / "tasks" / "TASK_018_UNIFIED_DATA_READINESS_CLOSURE.md",
        root / "reports" / "task_018_unified_data_readiness_closure.json",
        root / "reports" / "task_018_unified_data_readiness_closure.md",
        root / "reports" / "task_018d_real_readiness_gate_acceptance.json",
    ]
    # 循环处理：将 `required` 中的元素逐项绑定到 `path`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for path in required:
        require(path.exists(), f"缺少关闭文件：{path}")

    status_text = (root / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    required_status_fragments = [
        "阶段：统一数据质量门禁完成，进入市场状态识别MVP建设",
        "当前工作：关闭 TASK_018，并启动 TASK_019",
        "下一任务：TASK_019 市场状态输入合同与可解释基线",
        "- TASK_018：统一数据就绪度合同",
        "## 十一、TASK_018 最终状态",
        "## 十二、当前任务：TASK_019",
        "ReadinessGatedStandardDataService.query()",
        "TASK_018总状态：PASSED_WITH_WARNINGS",
        "## 十四、Git 与 GitHub 交付闭环",
    ]
    # 循环处理：将 `required_status_fragments` 中的元素逐项绑定到 `fragment`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for fragment in required_status_fragments:
        require(fragment in status_text, f"PROJECT_STATUS缺少：{fragment}")

    forbidden_status_fragments = [
        "当前工作：关闭 TASK_017，并启动 TASK_018",
        "下一任务：TASK_018 统一数据质量门禁与数据就绪度服务",
        "## 十一、当前任务：TASK_018",
    ]
    # 循环处理：将 `forbidden_status_fragments` 中的元素逐项绑定到 `fragment`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for fragment in forbidden_status_fragments:
        require(fragment not in status_text, f"PROJECT_STATUS仍含旧状态：{fragment}")

    closure = load_json(root / "reports" / "task_018_unified_data_readiness_closure.json")
    require(closure.get("task_id") == "TASK_018", "关闭报告task_id异常")
    require(closure.get("closure_status") == "PASSED_WITH_WARNINGS", "关闭状态异常")
    require(closure.get("database_write_operation_count") == 0, "关闭报告写操作必须为0")
    require(closure.get("next_task", {}).get("task_id") == "TASK_019", "下一任务异常")

    real = closure.get("real_acceptance", {})
    # 循环处理：将 `EXPECTED_REAL.items()` 中的元素逐项绑定到 `(key, expected)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for key, expected in EXPECTED_REAL.items():
        require(real.get(key) == expected, f"关闭报告真实验收字段异常：{key}")
    require(real.get("issues") == [], "关闭报告issues必须为空")

    source = load_json(root / "reports" / "task_018d_real_readiness_gate_acceptance.json")
    require(source.get("task_id") == "TASK_018D", "TASK_018D源报告task_id异常")
    require(source.get("overall_status") == "PASSED_WITH_WARNINGS", "TASK_018D源报告状态异常")
    # 循环处理：将 `EXPECTED_REAL.items()` 中的元素逐项绑定到 `(key, expected)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for key, expected in EXPECTED_REAL.items():
        require(source.get(key) == expected, f"TASK_018D源报告字段异常：{key}")
    require(source.get("issues") == [], "TASK_018D源报告issues必须为空")

    architecture = closure.get("architecture_result", {})
    require(architecture.get("mandatory_entrypoint") == "ReadinessGatedStandardDataService", "统一入口异常")
    require(architecture.get("raw_access_forbidden_for_downstream") is True, "Raw绕过必须禁止")
    require(architecture.get("provider_gate_cannot_be_skipped") is True, "Provider门禁不得跳过")
    require(architecture.get("readiness_gate_cannot_be_skipped") is True, "就绪度门禁不得跳过")
    require(architecture.get("market_state_must_use_gated_service") is True, "市场状态必须使用门禁服务")

    print(json.dumps({
        "task_id": "TASK_018",
        "overall_status": "PASSED",
        "closure_status": closure["closure_status"],
        "subtask_count": len(closure.get("subtasks", {})),
        "provider_count": real["provider_count"],
        "dataset_count": real["dataset_count"],
        "usage_count": real["usage_count"],
        "assessment_count": real["assessment_count"],
        "evidence_dimension_count": real["evidence_dimension_count"],
        "current_research_usable_count": real["current_research_usable_count"],
        "manual_decision_block_count": real["manual_decision_block_count"],
        "strict_historical_block_count": real["strict_historical_block_count"],
        "historical_training_block_count": real["historical_training_block_count"],
        "database_readonly_query_mode": real["database_readonly_query_mode"],
        "write_operation_count": real["write_operation_count"],
        "next_task": closure["next_task"]["task_id"],
    }, ensure_ascii=False, indent=2))
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
