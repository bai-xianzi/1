#!/usr/bin/env python3
# 本脚本核心功能：运行TASK_023B Windows机器级Provider环境盘点并写出本地JSON报告。
# - 不导入任何供应商SDK；
# - 不联网、不登录、不读取秘密值；
# - 不修改注册表、数据库或Provider激活状态。
"""运行TASK_023B Windows机器级Provider环境盘点。"""

from __future__ import annotations

import argparse
from pathlib import Path

from a_stock_quant.provider_environment_discovery import load_provider_discovery_manifest
from a_stock_quant.provider_windows_inventory import (
    build_windows_inventory_report,
    build_windows_provider_findings,
    collect_installed_applications,
    collect_python_interpreter_evidence,
    load_windows_inventory_rules,
    write_windows_inventory_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="configs/providers/provider_discovery_targets_v0.json",
        help="TASK_023A Provider manifest path.",
    )
    parser.add_argument(
        "--rules",
        default="configs/providers/provider_windows_inventory_rules_v0.json",
        help="TASK_023B Windows inventory rules path.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Local UTF-8 JSON report path. This report must not be committed automatically.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = load_provider_discovery_manifest(args.manifest)
    rules = load_windows_inventory_rules(args.rules)
    module_names = tuple(
        sorted(
            {
                module_name
                for target in targets
                for module_name in target.python_module_candidates
            }
        )
    )
    interpreters = collect_python_interpreter_evidence(module_names)
    applications = collect_installed_applications()
    findings = build_windows_provider_findings(
        targets,
        rules,
        interpreters,
        applications,
    )
    report = build_windows_inventory_report(findings, interpreters, applications)
    output = write_windows_inventory_report(report, Path(args.output))

    print(f"TASK_023B provider count: {report['provider_count']}")
    print(
        "Providers with local evidence: "
        f"{report['providers_with_local_evidence_count']}"
    )
    print(f"Python interpreter count: {report['python_interpreter_count']}")
    print(f"Selection status: {report['selection_status']}")
    print(f"Candidates: {report['recommended_task_023c_provider_ids']}")
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
