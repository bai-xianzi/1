# 本文件核心功能：实现 `finalize_task_022_status.py` 在TASK_022至TASK_024范围内的单一任务职责。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具，不读取未声明秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：维护者先理解边界再阅读实现，可防止第三方聚合源或交易能力被误升为主链。

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
# 本段代码核心功能：定义 `main`，执行 `finalize_task_022_status.py` 的命令行主流程并返回标准退出码。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `int`；测试函数通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    path = root / "PROJECT_STATUS.md"
    text = path.read_text(encoding="utf-8-sig")
    # 本段代码核心功能：根据条件 `TASK_SECTION_START not in text or TASK_SECTION_END not in text` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

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
# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式和此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    raise SystemExit(main())
