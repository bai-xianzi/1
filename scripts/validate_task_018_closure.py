from __future__ import annotations

import argparse
import json
from pathlib import Path


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict:
    require(path.exists(), f"缺少文件：{path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON根节点必须是对象：{path}")
    return value


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
    for fragment in required_status_fragments:
        require(fragment in status_text, f"PROJECT_STATUS缺少：{fragment}")

    forbidden_status_fragments = [
        "当前工作：关闭 TASK_017，并启动 TASK_018",
        "下一任务：TASK_018 统一数据质量门禁与数据就绪度服务",
        "## 十一、当前任务：TASK_018",
    ]
    for fragment in forbidden_status_fragments:
        require(fragment not in status_text, f"PROJECT_STATUS仍含旧状态：{fragment}")

    closure = load_json(root / "reports" / "task_018_unified_data_readiness_closure.json")
    require(closure.get("task_id") == "TASK_018", "关闭报告task_id异常")
    require(closure.get("closure_status") == "PASSED_WITH_WARNINGS", "关闭状态异常")
    require(closure.get("database_write_operation_count") == 0, "关闭报告写操作必须为0")
    require(closure.get("next_task", {}).get("task_id") == "TASK_019", "下一任务异常")

    real = closure.get("real_acceptance", {})
    for key, expected in EXPECTED_REAL.items():
        require(real.get(key) == expected, f"关闭报告真实验收字段异常：{key}")
    require(real.get("issues") == [], "关闭报告issues必须为空")

    source = load_json(root / "reports" / "task_018d_real_readiness_gate_acceptance.json")
    require(source.get("task_id") == "TASK_018D", "TASK_018D源报告task_id异常")
    require(source.get("overall_status") == "PASSED_WITH_WARNINGS", "TASK_018D源报告状态异常")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
