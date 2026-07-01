# 本脚本核心功能：在全部验收通过后，把 TASK_022 的权威状态从“待 Git 闭环”更新为关闭。
# - 输入：项目根目录中的 PROJECT_STATUS.md。
# - 输出：只替换 TASK_022 受控区块，不改变其他任务历史。
# - 为什么这样写：状态关闭必须发生在提交前的最后一步，避免真实验收尚未通过时提前宣告完成。
"""完成 TASK_022 状态区块，供提交脚本在 Git 闭环前调用。"""
from __future__ import annotations

import argparse
from pathlib import Path

TASK_SECTION_START = "<!-- TASK_022_STATUS_START -->"
TASK_SECTION_END = "<!-- TASK_022_STATUS_END -->"


# 主状态关闭流程：验证受控标记存在，再用稳定文本替换该任务区块。
# - 输入：--project-root 指向已完成全部验证的项目仓库。
# - 输出：PROJECT_STATUS.md 中 TASK_022 状态变为 CLOSED。
# - 为什么这样写：标记式替换比全文正则更安全，也能在重复执行时保持幂等。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    path = root / "PROJECT_STATUS.md"
    text = path.read_text(encoding="utf-8-sig")
    if TASK_SECTION_START not in text or TASK_SECTION_END not in text:
        raise RuntimeError("PROJECT_STATUS.md 缺少 TASK_022 受控状态区块。")
    block = f"""{TASK_SECTION_START}

## TASK_022：DolphinDB Provider 正式激活与真实注册表路由回归

- 状态：`CLOSED`
- 真实验收：`PASSED` 或 `PASSED_WITH_WARNINGS`
- 验收报告：`reports/task_022_real_dolphindb_provider_activation.json`
- 教学式注释审计：`reports/task_022_teaching_comment_audit.json`
- 安全边界：只读；数据库写操作为 0；未启用交易能力。
- 阶段终点：本状态文件与 TASK_022 全部成果将由完成脚本提交并推送到 GitHub `main`。

{TASK_SECTION_END}"""
    before = text.split(TASK_SECTION_START, 1)[0].rstrip()
    after = text.split(TASK_SECTION_END, 1)[1].lstrip()
    updated = before + "\n\n" + block + ("\n\n" + after if after else "\n")
    path.write_text(updated, encoding="utf-8", newline="\n")
    print("TASK_022 状态已更新为 CLOSED，等待 Git 提交和推送。")
    return 0


# 脚本入口：向 PowerShell 返回标准退出码。
# - 输入：操作系统命令行参数。
# - 为什么这样写：状态写入失败时必须阻断后续 git add、commit 和 push。
if __name__ == "__main__":
    raise SystemExit(main())
