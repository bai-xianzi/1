from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUS_MARKER = "<!-- TASK_019_CLOSURE_START -->"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}根节点必须是对象")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    closure_path = (
        root
        / "reports"
        / "task_019_market_state_research_mvp_closure.json"
    )
    task_019c_path = (
        root
        / "reports"
        / "task_019c_real_market_state_feature_acceptance.json"
    )
    task_019d_path = (
        root
        / "reports"
        / "task_019d_research_market_state_scoring_acceptance.json"
    )
    status_path = root / "PROJECT_STATUS.md"

    for path in (
        closure_path,
        task_019c_path,
        task_019d_path,
        status_path,
        root
        / "tasks"
        / "TASK_019_MARKET_STATE_RESEARCH_MVP_CLOSURE.md",
        root
        / "reports"
        / "task_019_market_state_research_mvp_closure.md",
    ):
        require(path.exists(), f"缺少文件：{path}")

    closure = read_json(closure_path)
    task_019c = read_json(task_019c_path)
    task_019d = read_json(task_019d_path)

    require(closure["task_id"] == "TASK_019", "task_id异常")
    require(
        closure["overall_status"] == "CLOSED_WITH_WARNINGS",
        "关闭状态异常",
    )
    require(closure["scope"] == "RESEARCH_ONLY", "用途范围异常")
    require(len(closure["closed_subtasks"]) == 4, "子任务数量异常")
    require(
        {item["task_id"] for item in closure["closed_subtasks"]}
        == {"TASK_019A", "TASK_019B", "TASK_019C", "TASK_019D"},
        "关闭子任务集合异常",
    )

    require(
        task_019c["overall_status"] == "PASSED_WITH_WARNINGS",
        "TASK_019C状态异常",
    )
    require(
        task_019c["generated_feature_count"] == 15,
        "TASK_019C特征数量异常",
    )
    require(
        task_019c["generated_feature_family_count"] == 5,
        "TASK_019C特征族数量异常",
    )
    require(task_019c["issues"] == [], "TASK_019C存在issues")
    require(
        task_019c["database_readonly_query_mode"] is True,
        "TASK_019C不是真实只读模式",
    )
    require(
        task_019c["write_operation_count"] == 0,
        "TASK_019C存在写操作",
    )

    require(
        task_019d["overall_status"] == "PASSED_WITH_WARNINGS",
        "TASK_019D状态异常",
    )
    require(
        task_019d["policy_status"]
        == "RESEARCH_HYPOTHESIS_UNVALIDATED",
        "TASK_019D政策状态异常",
    )
    require(
        task_019d["candidate_state"]
        == "STALE_INPUT_INDETERMINATE",
        "TASK_019D过期候选状态异常",
    )
    require(
        task_019d["calendar_age_days"] == 178,
        "TASK_019D日历滞后异常",
    )
    require(task_019d["issues"] == [], "TASK_019D存在issues")
    require(
        task_019d["candidate_state_actionable"] is False,
        "候选状态被错误设为可执行",
    )
    require(
        task_019d["manual_decision_allowed"] is False,
        "人工决策被错误放行",
    )
    require(
        task_019d["official_market_state_allowed"] is False,
        "正式市场状态被错误放行",
    )
    require(
        task_019d["trade_execution_allowed"] is False,
        "交易执行被错误放行",
    )
    require(
        task_019d["write_operation_count"] == 0,
        "TASK_019D存在写操作",
    )

    invariants = closure["closure_invariants"]
    require(invariants["feature_count"] == 15, "关闭特征数量异常")
    require(
        invariants["feature_family_count"] == 5,
        "关闭特征族数量异常",
    )
    require(
        invariants["formal_regime_label_allowed"] is False,
        "正式状态标签被错误放行",
    )
    require(
        invariants["database_write_operation_count"] == 0,
        "关闭报告存在数据库写操作",
    )
    require(
        closure["next_task"]["task_id"] == "TASK_020",
        "下一任务异常",
    )
    require(
        STATUS_MARKER in status_path.read_text(encoding="utf-8"),
        "PROJECT_STATUS缺少TASK_019关闭记录",
    )

    output = {
        "task_id": "TASK_019",
        "overall_status": "PASSED",
        "closure_status": closure["overall_status"],
        "closed_subtask_count": len(closure["closed_subtasks"]),
        "real_feature_count": task_019c["generated_feature_count"],
        "feature_family_count": task_019c[
            "generated_feature_family_count"
        ],
        "research_candidate_state": task_019d["candidate_state"],
        "candidate_state_actionable": task_019d[
            "candidate_state_actionable"
        ],
        "manual_decision_allowed": task_019d[
            "manual_decision_allowed"
        ],
        "official_market_state_allowed": task_019d[
            "official_market_state_allowed"
        ],
        "trade_execution_allowed": task_019d[
            "trade_execution_allowed"
        ],
        "database_write_operation_count": 0,
        "next_task": closure["next_task"]["task_id"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
