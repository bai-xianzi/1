# 本脚本核心功能：验证TASK_021A权威文件、机器政策、迁移盘点和提交阻断状态是否完整。
# - argparse接收项目根目录，确保脚本可以在任意当前目录运行。
# - json读取快照盘点报告，核对文件数量和迁移规模。
# - load_code_comment_policy执行机器政策数据合同校验。
# - 为什么这样写：在开始修改上百个文件前，必须先证明规则和基线是可靠的。
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.code_comment_policy import (
    CommentMigrationStatus,
    load_code_comment_policy,
)


# 权威文件标记：每个长期文件必须包含唯一TASK_021A标记。
# - 标记用于防止重复追加，也让验证器能够精确定位规则是否落盘。
# - 为什么这样写：仅检查自然语言关键词容易误判，唯一标记更稳定。
AUTHORITY_MARKERS = {
    "PROJECT_MEMORY.md": "<!-- TASK_021A_COMMENT_MEMORY -->",
    "DEVELOPMENT_GUIDANCE.md": (
        "<!-- TASK_021A_COMMENT_GUIDANCE -->"
    ),
    "AGENTS.md": "<!-- TASK_021A_COMMENT_AGENTS -->",
    "SYSTEM_ARCHITECTURE.md": (
        "<!-- TASK_021A_COMMENT_ARCHITECTURE -->"
    ),
    "PROJECT_STATUS.md": "<!-- TASK_021A_COMMENT_STATUS -->",
    "CODEX_EXECUTION_POLICY.md": (
        "<!-- TASK_021A_COMMENT_CODEX -->"
    ),
}


# 条件断言：条件为False时抛出带中文说明的RuntimeError。
# - condition是需要满足的布尔表达式。
# - message说明失败的具体合同。
# - 为什么这样写：集中错误处理让验证逻辑保持清晰，并确保PowerShell收到非零退出码。
def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


# 主验证流程：加载政策和盘点，检查权威标记、统计数字和Git门禁。
# - 快照中包含102个Python文件和21个PowerShell文件，总计123个迁移目标。
# - 统计值来自用户上传的当前本地代码快照，不来自公开GitHub旧版本。
# - 为什么这样写：用真实本地基线锁定迁移范围，避免遗漏尚未推送或刚提交的代码。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    policy = load_code_comment_policy(
        root
        / "configs"
        / "engineering"
        / "code_comment_policy_v0.json"
    )
    inventory = json.loads(
        (
            root
            / "reports"
            / "task_021a_comment_migration_inventory.json"
        ).read_text(encoding="utf-8")
    )

    require(
        (root / "CODE_COMMENTING_STANDARD.md").exists(),
        "缺少代码注释最高权威标准。",
    )
    for relative_path, marker in AUTHORITY_MARKERS.items():
        path = root / relative_path
        require(path.exists(), f"缺少权威文件：{relative_path}")
        require(
            marker in path.read_text(encoding="utf-8"),
            f"{relative_path}缺少TASK_021A标记。",
        )

    require(
        policy.migration.status
        is CommentMigrationStatus.IN_PROGRESS,
        "初始迁移状态必须为IN_PROGRESS。",
    )
    require(
        policy.migration.batch_count == 6,
        "迁移批次数量异常。",
    )
    require(
        policy.migration.github_commit_blocked_until_full_migration,
        "全量迁移完成前必须阻断Git提交。",
    )
    require(
        policy.git_gate.user_confirmation_required_before_commit,
        "Git提交前必须等待用户确认。",
    )
    require(
        policy.git_gate.user_confirmation_required_before_push,
        "Git推送前必须等待用户确认。",
    )

    summary = inventory["summary"]
    require(
        summary["human_authored_code_file_count"] == 123,
        "人工代码文件数量异常。",
    )
    require(
        summary["python_file_count"] == 102,
        "Python文件数量异常。",
    )
    require(
        summary["powershell_file_count"] == 21,
        "PowerShell文件数量异常。",
    )
    require(
        summary["migration_required_file_count"] == 123,
        "迁移目标数量异常。",
    )
    require(
        summary["github_commit_blocked"] is True,
        "盘点报告没有阻断Git提交。",
    )

    output = {
        "task_id": "TASK_021A",
        "overall_status": "PASSED",
        "policy_version": policy.policy_version,
        "migration_status": policy.migration.status.value,
        "migration_batch_count": policy.migration.batch_count,
        "human_authored_code_file_count": (
            summary["human_authored_code_file_count"]
        ),
        "python_file_count": summary["python_file_count"],
        "powershell_file_count": summary["powershell_file_count"],
        "total_line_count": summary["total_line_count"],
        "total_comment_line_count": (
            summary["total_comment_line_count"]
        ),
        "github_commit_blocked": (
            policy.migration.github_commit_blocked_until_full_migration
        ),
        "github_push_blocked_until_user_confirmation": (
            policy.migration.github_push_blocked_until_user_confirmation
        ),
        "user_confirmation_required_before_commit": (
            policy.git_gate.user_confirmation_required_before_commit
        ),
        "user_confirmation_required_before_push": (
            policy.git_gate.user_confirmation_required_before_push
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


# 脚本入口：将验证结果转换为标准进程退出码。
# - 成功返回0，任何合同异常通过未捕获异常返回非零。
# - 为什么这样写：PowerShell能够可靠阻断后续迁移或提交步骤。
if __name__ == "__main__":
    raise SystemExit(main())
