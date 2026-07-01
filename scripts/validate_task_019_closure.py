# 本脚本核心功能：验证任务019关闭验收的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path


# 配置常量：集中定义 `STATUS_MARKER`，供后续流程复用。
# - 当前值或构造表达式：`'<!-- TASK_019_CLOSURE_START -->'`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
STATUS_MARKER = "<!-- TASK_019_CLOSURE_START -->"


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


# 函数 `read_json`：完成读取JSON相关处理。
# - 输入：path。
# - 处理：完成读取JSON相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}根节点必须是对象")
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

    # 循环处理：将 `(closure_path, task_019c_path, task_019d_path, status_path, root / 'tasks' / 'TASK_019_...` 中的元素逐项绑定到 `path`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
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
