#!/usr/bin/env python3
"""Audit tracked Git text files for UTF-8 and common Chinese mojibake.

This script is read-only. It does not modify repository files.

Run from the repository root:

    python scripts/audit_git_encoding.py
"""
# 本脚本核心功能：审计Git跟踪文本的UTF-8编码与常见中文乱码风险。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 配置常量：集中定义 `TEXT_EXTENSIONS`，供后续流程复用。
# - 当前值或构造表达式：`{'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.ps...`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".conf", ".ps1", ".bat", ".cmd", ".sh",
    ".sql", ".csv", ".tsv", ".xml", ".html", ".css", ".js",
    ".ts", ".tsx", ".jsx",
}

# Common fragments produced when UTF-8 Chinese bytes are decoded as GBK/ANSI
# and then saved again. This is only a warning heuristic.
# 配置常量：集中定义 `MOJIBAKE_MARKERS`，供后续流程复用。
# - 当前值或构造表达式：`('锛', '銆', '鈥', '鈿', '姝', '鏇', '杩', '寮', '绔', '鏍', '璇', '鏂', '缁', '缂', '浠', '浣', '鎴', '...`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
MOJIBAKE_MARKERS = (
    "锛", "銆", "鈥", "鈿", "姝", "鏇", "杩", "寮", "绔",
    "鏍", "璇", "鏂", "缁", "缂", "浠", "浣", "鎴", "鍙",
    "涓", "鐨", "妫", "鏌", "鎵", "瀹", "璐", "鏁", "鎹",
    "闂", "棰", "杈", "鍑", "绾", "褰", "鐘", "鎬",
)

# This source file intentionally contains the marker literals above.
# It must still be checked for valid UTF-8, but must not be scored by the
# mojibake-marker heuristic, otherwise it will always report itself.
# 配置常量：集中定义 `MOJIBAKE_HEURISTIC_EXCLUDES`，供后续流程复用。
# - 当前值或构造表达式：`{'scripts/audit_git_encoding.py'}`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
MOJIBAKE_HEURISTIC_EXCLUDES = {
    "scripts/audit_git_encoding.py",
}


# 函数 `tracked_files`：完成trackedfiles相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成trackedfiles相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `list[Path]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    # 输出结果：返回 `[Path(item.decode('utf-8', errors='surrogateescape')) for item in result.stdout.split(b...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return [
        Path(item.decode("utf-8", errors="surrogateescape"))
        for item in result.stdout.split(b"\0")
        if item
    ]


# 函数 `is_probably_text`：完成isprobablytext相关处理。
# - 输入：path、data。
# - 处理：完成isprobablytext相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `bool`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def is_probably_text(path: Path, data: bytes) -> bool:
    # 条件分支：检查 `path.suffix.lower() in TEXT_EXTENSIONS` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if path.suffix.lower() in TEXT_EXTENSIONS:
        # 输出结果：返回 `True` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return True
    # 条件分支：检查 `b'\x00' in data[:8192]` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if b"\0" in data[:8192]:
        # 输出结果：返回 `False` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return False
    # 输出结果：返回 `len(data) <= 2000000` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return len(data) <= 2_000_000


# 函数 `should_run_mojibake_heuristic`：完成should运行mojibakeheuristic相关处理。
# - 输入：path。
# - 处理：完成should运行mojibakeheuristic相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `bool`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def should_run_mojibake_heuristic(path: Path) -> bool:
    # 输出结果：返回 `path.as_posix() not in MOJIBAKE_HEURISTIC_EXCLUDES` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return path.as_posix() not in MOJIBAKE_HEURISTIC_EXCLUDES


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
    # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
    # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
    try:
        files = tracked_files()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: unable to read Git tracked files: {exc}")
        # 输出结果：返回 `2` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return 2

    utf8_ok = 0
    utf8_bom: list[str] = []
    non_utf8: list[tuple[str, str]] = []
    suspicious: list[tuple[str, int, int]] = []
    missing: list[str] = []

    # 循环处理：将 `files` 中的元素逐项绑定到 `path`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for path in files:
        # 条件分支：检查 `not path.exists()` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not path.exists():
            missing.append(str(path))
            continue

        data = path.read_bytes()
        # 条件分支：检查 `not is_probably_text(path, data)` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not is_probably_text(path, data):
            continue

        has_bom = data.startswith(b"\xef\xbb\xbf")
        # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
        # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
        # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
        try:
            text = data.decode("utf-8-sig" if has_bom else "utf-8")
        except UnicodeDecodeError as exc:
            non_utf8.append((str(path), str(exc)))
            continue

        utf8_ok += 1
        # 条件分支：检查 `has_bom` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if has_bom:
            utf8_bom.append(str(path))

        # 条件分支：检查 `should_run_mojibake_heuristic(path)` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if should_run_mojibake_heuristic(path):
            marker_count = sum(
                text.count(marker)
                for marker in MOJIBAKE_MARKERS
            )
            replacement_count = text.count("\ufffd")

            # 条件分支：检查 `marker_count >= 3 or replacement_count > 0` 后选择对应处理路径。
            # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
            # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
            if marker_count >= 3 or replacement_count > 0:
                suspicious.append(
                    (
                        str(path),
                        marker_count,
                        replacement_count,
                    )
                )

    print("=== Git text encoding audit ===")
    print(f"Tracked files          : {len(files)}")
    print(f"UTF-8 text files       : {utf8_ok}")
    print(f"UTF-8 files with BOM   : {len(utf8_bom)}")
    print(f"Non-UTF-8 text files   : {len(non_utf8)}")
    print(f"Suspicious mojibake    : {len(suspicious)}")
    print(f"Missing tracked files  : {len(missing)}")

    # 条件分支：检查 `utf8_bom` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if utf8_bom:
        print("\n[UTF-8 BOM]")
        # 循环处理：将 `utf8_bom` 中的元素逐项绑定到 `item`。
        # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
        # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
        for item in utf8_bom:
            print(item)

    # 条件分支：检查 `non_utf8` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if non_utf8:
        print("\n[NON-UTF8]")
        # 循环处理：将 `non_utf8` 中的元素逐项绑定到 `(item, error)`。
        # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
        # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
        for item, error in non_utf8:
            print(f"{item}: {error}")

    # 条件分支：检查 `suspicious` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if suspicious:
        print("\n[SUSPICIOUS MOJIBAKE]")
        # 循环处理：将 `suspicious` 中的元素逐项绑定到 `(item, markers, replacements)`。
        # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
        # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
        for item, markers, replacements in suspicious:
            print(
                f"{item}: marker_count={markers}, "
                f"replacement_chars={replacements}"
            )

    # 条件分支：检查 `missing` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if missing:
        print("\n[MISSING]")
        # 循环处理：将 `missing` 中的元素逐项绑定到 `item`。
        # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
        # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
        for item in missing:
            print(item)

    # 条件分支：检查 `non_utf8 or suspicious` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if non_utf8 or suspicious:
        print(
            "\nRESULT: REVIEW REQUIRED. "
            "Do not mass-convert files before checking the listed paths."
        )
        # 输出结果：返回 `1` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return 1

    print("\nRESULT: PASSED. Tracked text files are valid UTF-8.")
    # 输出结果：返回 `0` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    sys.exit(main())
