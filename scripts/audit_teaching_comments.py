# 本脚本核心功能：扫描人工编写的Python和PowerShell文件，生成教学式注释覆盖率与缺口报告。
# - argparse读取项目根目录、政策文件、输出文件和审计模式。
# - ast解析Python语法树，定位类、函数和异步函数定义。
# - re识别PowerShell函数和教学式注释标记。
# - inventory模式只生成迁移清单并返回成功；enforce模式在发现违规时返回非零退出码。
# - 为什么这样写：历史代码需要分批迁移，但新代码和最终全仓库门禁必须由同一个审计器执行。
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from a_stock_quant.code_comment_policy import (
    CommentMigrationStatus,
    load_code_comment_policy,
)


# 文件级审计结果：记录代码量、注释量、定义数量和具体违规。
# - violations保存可操作的行号和原因，不只返回一个布尔值。
# - compliant只有在violations为空时为True。
# - 为什么这样写：迁移需要知道“哪一行缺什么”，否则无法按批次稳定修复。
@dataclass(frozen=True, slots=True)
class FileCommentAudit:
    path: str
    language: str
    line_count: int
    code_line_count: int
    comment_line_count: int
    teaching_detail_line_count: int
    reason_line_count: int
    definition_count: int
    violations: tuple[str, ...]

    # 合规属性：把违规列表是否为空转换为直观布尔结果。
    # - 没有缓存额外状态，避免compliant和violations出现矛盾。
    # - 为什么这样写：单一事实来源更适合审计和测试。
    @property
    def compliant(self) -> bool:
        return not self.violations


# 前置注释窗口提取：读取目标代码行之前连续的单行注释和空行。
# - line_number使用AST的一基行号，转换为Python列表零基索引。
# - 最多回看12行，足够容纳概括、分点、常量和原因说明。
# - 遇到非注释代码立即停止，确保说明确实位于目标代码之前。
# - 为什么这样写：距离过远的注释可能解释的是其他代码，不能算作一一对应。
def _preceding_comment_window(
    lines: Sequence[str],
    line_number: int,
    *,
    maximum_lines: int = 12,
) -> tuple[str, ...]:
    index = line_number - 2
    collected: list[str] = []
    inspected = 0
    while index >= 0 and inspected < maximum_lines:
        text = lines[index]
        stripped = text.strip()
        inspected += 1
        if not stripped:
            collected.append(text)
            index -= 1
            continue
        if stripped.startswith("#"):
            collected.append(text)
            index -= 1
            continue
        break
    return tuple(reversed(collected))


# 教学式窗口判定：检查概括、`# -`分点和“为什么这样写”说明。
# - meaningful_comments排除空行，只保留真正的单行注释。
# - 第一项要求至少两行注释，防止一句模糊短句冒充教学块。
# - detail要求出现`# -`，对应用户要求的无序列表。
# - reason要求出现至少一种原因短语。
# - 为什么这样写：三个结构信号能以较低误报率识别最基本的教学式注释形态。
def _window_violations(
    window: Iterable[str],
    *,
    object_label: str,
    line_number: int,
) -> list[str]:
    meaningful_comments = [
        line.strip()
        for line in window
        if line.strip().startswith("#")
    ]
    violations: list[str] = []
    if len(meaningful_comments) < 2:
        violations.append(
            f"line {line_number}: {object_label}前缺少多行教学式注释"
        )
    if not any(
        line.startswith("# -")
        for line in meaningful_comments
    ):
        violations.append(
            f"line {line_number}: {object_label}前缺少# -分点说明"
        )
    if not any(
        phrase in line
        for phrase in (
            "为什么这样写",
            "为什么要这样写",
            "为什么要这一步",
        )
        for line in meaningful_comments
    ):
        violations.append(
            f"line {line_number}: {object_label}前缺少为什么这样写"
        )
    return violations


# Python文件审计：解析语法树并检查模块代码量、类和函数前置说明。
# - ast.parse保证只对语法有效的Python进行结构检查。
# - ClassDef、FunctionDef和AsyncFunctionDef代表最重要的可复用逻辑边界。
# - 注释统计使用物理行，定义检查使用AST逻辑节点。
# - 为什么这样写：AST比正则更可靠，能够正确处理装饰器、异步函数和多行签名。
def audit_python_file(
    project_root: Path,
    path: Path,
) -> FileCommentAudit:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    comment_lines = [
        line for line in lines if line.lstrip().startswith("#")
    ]
    blank_count = sum(1 for line in lines if not line.strip())
    code_line_count = (
        len(lines) - len(comment_lines) - blank_count
    )
    violations: list[str] = []
    definition_count = 0

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        violations.append(
            f"line {exc.lineno}: Python语法错误：{exc.msg}"
        )
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                definition_count += 1
                # 装饰器定位：把类的教学式注释窗口起点移动到第一个装饰器，而不是class关键字本身。
                # - decorator_list保存@dataclass等装饰器；没有装饰器时只使用node.lineno。
                # - 数据变化：first_line是一个一基行号，不修改语法树或源代码内容。
                # - 为什么这样写：教学式注释必须放在装饰器之前，否则装饰器会截断前置注释窗口并产生误报。
                first_line = min(
                    [node.lineno]
                    + [
                        decorator.lineno
                        for decorator in node.decorator_list
                    ]
                )
                violations.extend(
                    _window_violations(
                        _preceding_comment_window(
                            lines,
                            first_line,
                        ),
                        object_label=f"类{node.name}",
                        line_number=first_line,
                    )
                )
            elif isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                definition_count += 1
                first_line = min(
                    [node.lineno]
                    + [
                        decorator.lineno
                        for decorator in node.decorator_list
                    ]
                )
                violations.extend(
                    _window_violations(
                        _preceding_comment_window(
                            lines,
                            first_line,
                        ),
                        object_label=f"函数{node.name}",
                        line_number=first_line,
                    )
                )

    relative_path = path.relative_to(project_root).as_posix()
    return FileCommentAudit(
        path=relative_path,
        language="python",
        line_count=len(lines),
        code_line_count=code_line_count,
        comment_line_count=len(comment_lines),
        teaching_detail_line_count=sum(
            line.lstrip().startswith("# -")
            for line in comment_lines
        ),
        reason_line_count=sum(
            any(
                phrase in line
                for phrase in (
                    "为什么这样写",
                    "为什么要这样写",
                    "为什么要这一步",
                )
            )
            for line in comment_lines
        ),
        definition_count=definition_count,
        violations=tuple(violations),
    )


# PowerShell文件审计：识别函数定义并检查其前置教学式注释。
# - 正则只匹配行首function关键字，避免把字符串内容误判为函数。
# - PowerShell脚本当前多数是顺序执行脚本，因此函数数量可能为0，但仍统计整体注释覆盖率。
# - 为什么这样写：先建立稳定的函数级审计，再在后续批次增加分支和命令块级规则，降低一次性误报。
def audit_powershell_file(
    project_root: Path,
    path: Path,
) -> FileCommentAudit:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    comment_lines = [
        line for line in lines if line.lstrip().startswith("#")
    ]
    blank_count = sum(1 for line in lines if not line.strip())
    code_line_count = (
        len(lines) - len(comment_lines) - blank_count
    )
    violations: list[str] = []
    definition_count = 0

    for index, line in enumerate(lines, start=1):
        match = re.match(
            r"^\s*function\s+([A-Za-z0-9_-]+)",
            line,
            re.IGNORECASE,
        )
        if match is None:
            continue
        definition_count += 1
        violations.extend(
            _window_violations(
                _preceding_comment_window(lines, index),
                object_label=f"PowerShell函数{match.group(1)}",
                line_number=index,
            )
        )

    if code_line_count > 0 and not comment_lines:
        violations.append(
            "line 1: 脚本包含可执行代码但没有任何教学式单行注释"
        )

    relative_path = path.relative_to(project_root).as_posix()
    return FileCommentAudit(
        path=relative_path,
        language="powershell",
        line_count=len(lines),
        code_line_count=code_line_count,
        comment_line_count=len(comment_lines),
        teaching_detail_line_count=sum(
            line.lstrip().startswith("# -")
            for line in comment_lines
        ),
        reason_line_count=sum(
            any(
                phrase in line
                for phrase in (
                    "为什么这样写",
                    "为什么要这样写",
                    "为什么要这一步",
                )
            )
            for line in comment_lines
        ),
        definition_count=definition_count,
        violations=tuple(violations),
    )


# 文件发现：只返回项目内人工Python和PowerShell文件，并排除缓存与虚拟环境。
# - rglob递归遍历项目目录。
# - parts集合用于快速识别被排除的目录名。
# - 结果按POSIX相对路径排序，保证不同机器生成相同顺序。
# - 为什么这样写：稳定顺序使审计报告可比较，也避免把第三方环境误纳入迁移。
def discover_code_files(
    project_root: Path,
) -> tuple[Path, ...]:
    excluded_parts = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "archive",
        "data",
        "logs",
    }
    paths = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(project_root)
        if excluded_parts.intersection(relative.parts):
            continue
        if path.suffix.lower() not in {".py", ".ps1"}:
            continue
        paths.append(path)
    return tuple(
        sorted(
            paths,
            key=lambda item: item.relative_to(
                project_root
            ).as_posix(),
        )
    )


# 命令行参数：定义项目根目录、政策文件、输出文件和审计模式。
# - inventory允许历史代码不合规但生成完整报告。
# - enforce在任何文件违规时返回退出码1，供Git门禁使用。
# - 为什么这样写：同一套扫描逻辑服务迁移盘点和最终强制门禁，避免统计口径不一致。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument(
        "--policy",
        default=(
            "configs/engineering/"
            "code_comment_policy_v0.json"
        ),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        choices=("inventory", "enforce"),
        default="inventory",
    )
    return parser


# 主流程：加载政策、扫描文件、汇总报告并根据模式返回退出码。
# - 项目根目录和输出路径都转换为绝对Path。
# - 每个文件按扩展名分派给对应审计函数。
# - 报告记录合规数量、违规数量、迁移状态和Git阻断状态。
# - 为什么这样写：退出码和JSON报告同时提供机器门禁与人工排查能力。
def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    policy_path = (
        project_root / args.policy
        if not Path(args.policy).is_absolute()
        else Path(args.policy)
    )
    output_path = Path(args.output).resolve()

    policy = load_code_comment_policy(policy_path)
    audits: list[FileCommentAudit] = []
    for path in discover_code_files(project_root):
        if path.suffix.lower() == ".py":
            audits.append(
                audit_python_file(project_root, path)
            )
        else:
            audits.append(
                audit_powershell_file(project_root, path)
            )

    compliant_count = sum(item.compliant for item in audits)
    violation_count = sum(
        len(item.violations) for item in audits
    )
    report = {
        "task_id": policy.task_id,
        "policy_version": policy.policy_version,
        "mode": args.mode,
        "migration_status": policy.migration.status.value,
        "file_count": len(audits),
        "compliant_file_count": compliant_count,
        "non_compliant_file_count": (
            len(audits) - compliant_count
        ),
        "violation_count": violation_count,
        "github_commit_blocked": (
            policy.migration.github_commit_blocked_until_full_migration
        ),
        "github_push_blocked_until_user_confirmation": (
            policy.migration.github_push_blocked_until_user_confirmation
        ),
        "files": [asdict(item) for item in audits],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(
        {
            key: value
            for key, value in report.items()
            if key != "files"
        },
        ensure_ascii=False,
        indent=2,
    ))

    if args.mode == "inventory":
        return 0
    return 0 if violation_count == 0 else 1


# 脚本入口：把main返回值交给操作系统，供PowerShell和CI判断成功或失败。
# - SystemExit保留标准退出码语义。
# - 为什么这样写：门禁脚本不能只打印错误，必须让自动化流程真正停止。
if __name__ == "__main__":
    raise SystemExit(main())
