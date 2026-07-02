# 本脚本核心功能：在当前Python环境中运行TASK_023A离线Provider环境盘点并写出JSON报告。
# - 输入：发现清单路径和报告输出路径。
# - 输出：不含秘密值的环境发现报告；脚本不导入供应商SDK、不联网、不访问数据库。
"""运行TASK_023A外部Provider环境发现。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a_stock_quant.provider_environment_discovery import (  # noqa: E402
    build_provider_environment_report,
    discover_provider_environment,
    load_provider_discovery_manifest,
    write_provider_environment_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "configs/providers/provider_discovery_targets_v0.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/task_023_local_provider_environment_inventory.json",
    )
    args = parser.parse_args()

    targets = load_provider_discovery_manifest(args.manifest)
    findings = discover_provider_environment(targets)
    report = build_provider_environment_report(findings)
    output_path = write_provider_environment_report(report, args.output)

    print(f"TASK_023A provider count: {report['provider_count']}")
    print(f"Runtime present count: {report['runtime_present_count']}")
    print(f"Selection status: {report['selection_status']}")
    print(f"Report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
