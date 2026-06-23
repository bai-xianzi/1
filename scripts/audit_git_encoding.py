#!/usr/bin/env python3
"""Audit tracked Git text files for UTF-8 and common Chinese mojibake.

This script is read-only. It does not modify repository files.

Run from the repository root:

    python scripts/audit_git_encoding.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".conf", ".ps1", ".bat", ".cmd", ".sh",
    ".sql", ".csv", ".tsv", ".xml", ".html", ".css", ".js",
    ".ts", ".tsx", ".jsx",
}

# Common fragments produced when UTF-8 Chinese bytes are decoded as GBK/ANSI
# and then saved again. This is only a warning heuristic.
MOJIBAKE_MARKERS = (
    "锛", "銆", "鈥", "鈿", "姝", "鏇", "杩", "寮", "绔",
    "鏍", "璇", "鏂", "缁", "缂", "浠", "浣", "鎴", "鍙",
    "涓", "鐨", "妫", "鏌", "鎵", "瀹", "璐", "鏁", "鎹",
    "闂", "棰", "杈", "鍑", "绾", "褰", "鐘", "鎬",
)

# This source file intentionally contains the marker literals above.
# It must still be checked for valid UTF-8, but must not be scored by the
# mojibake-marker heuristic, otherwise it will always report itself.
MOJIBAKE_HEURISTIC_EXCLUDES = {
    "scripts/audit_git_encoding.py",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [
        Path(item.decode("utf-8", errors="surrogateescape"))
        for item in result.stdout.split(b"\0")
        if item
    ]


def is_probably_text(path: Path, data: bytes) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if b"\0" in data[:8192]:
        return False
    return len(data) <= 2_000_000


def should_run_mojibake_heuristic(path: Path) -> bool:
    return path.as_posix() not in MOJIBAKE_HEURISTIC_EXCLUDES


def main() -> int:
    try:
        files = tracked_files()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: unable to read Git tracked files: {exc}")
        return 2

    utf8_ok = 0
    utf8_bom: list[str] = []
    non_utf8: list[tuple[str, str]] = []
    suspicious: list[tuple[str, int, int]] = []
    missing: list[str] = []

    for path in files:
        if not path.exists():
            missing.append(str(path))
            continue

        data = path.read_bytes()
        if not is_probably_text(path, data):
            continue

        has_bom = data.startswith(b"\xef\xbb\xbf")
        try:
            text = data.decode("utf-8-sig" if has_bom else "utf-8")
        except UnicodeDecodeError as exc:
            non_utf8.append((str(path), str(exc)))
            continue

        utf8_ok += 1
        if has_bom:
            utf8_bom.append(str(path))

        if should_run_mojibake_heuristic(path):
            marker_count = sum(
                text.count(marker)
                for marker in MOJIBAKE_MARKERS
            )
            replacement_count = text.count("\ufffd")

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

    if utf8_bom:
        print("\n[UTF-8 BOM]")
        for item in utf8_bom:
            print(item)

    if non_utf8:
        print("\n[NON-UTF8]")
        for item, error in non_utf8:
            print(f"{item}: {error}")

    if suspicious:
        print("\n[SUSPICIOUS MOJIBAKE]")
        for item, markers, replacements in suspicious:
            print(
                f"{item}: marker_count={markers}, "
                f"replacement_chars={replacements}"
            )

    if missing:
        print("\n[MISSING]")
        for item in missing:
            print(item)

    if non_utf8 or suspicious:
        print(
            "\nRESULT: REVIEW REQUIRED. "
            "Do not mass-convert files before checking the listed paths."
        )
        return 1

    print("\nRESULT: PASSED. Tracked text files are valid UTF-8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
