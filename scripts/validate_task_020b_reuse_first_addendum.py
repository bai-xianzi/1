from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.reuse_first_policy import (
    load_reuse_first_policy,
)


AUTHORITY_MARKERS = {
    "PROJECT_MEMORY.md": "<!-- TASK_020B_REUSE_MEMORY -->",
    "SYSTEM_ARCHITECTURE.md": "<!-- TASK_020B_REUSE_ARCHITECTURE -->",
    "DEVELOPMENT_GUIDANCE.md": "<!-- TASK_020B_REUSE_GUIDANCE -->",
    "INSTITUTIONAL_RESEARCH_AND_EXECUTION_GOVERNANCE.md": (
        "<!-- TASK_020B_REUSE_GOVERNANCE -->"
    ),
    "AGENTS.md": "<!-- TASK_020B_REUSE_AGENTS -->",
    "PROJECT_STATUS.md": "<!-- TASK_020B_REUSE_STATUS -->",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    policy = load_reuse_first_policy(
        root
        / "configs"
        / "engineering"
        / "reuse_first_policy_v0.json"
    )

    require(
        (root / "REUSE_FIRST_ENGINEERING_POLICY.md").exists(),
        "缺少复用优先权威政策文件",
    )
    require(
        (
            root
            / "src"
            / "a_stock_quant"
            / "provider_plugin_protocol.py"
        ).exists(),
        "缺少TASK_020B Provider插件协议",
    )
    for relative_path, marker in AUTHORITY_MARKERS.items():
        path = root / relative_path
        require(path.exists(), f"缺少权威文件：{relative_path}")
        require(
            marker in path.read_text(encoding="utf-8"),
            f"{relative_path}缺少复用优先标记",
        )

    require(
        policy.principle == "REUSE_FIRST_CUSTOM_BUILD_LAST",
        "复用优先原则异常",
    )
    require(
        policy.reuse_order[-1]
        == "CUSTOM_IMPLEMENTATION_LAST_RESORT",
        "自研没有排在最后",
    )
    require(
        len(policy.required_assessment_sections) == 11,
        "复用评估分区数量异常",
    )
    require(
        len(policy.required_custom_build_evidence) == 6,
        "自研证据数量异常",
    )
    require(
        not policy.custom_implementation_default_allowed,
        "错误允许默认自研",
    )
    require(
        not policy.unknown_license_reuse_allowed,
        "错误允许未知许可证复用",
    )
    require(
        not policy.copy_without_provenance_allowed,
        "错误允许无来源复制",
    )
    require(
        not policy.vendor_sdk_reimplementation_allowed,
        "错误允许重写厂商SDK",
    )

    output = {
        "task_id": policy.task_id,
        "overall_status": "PASSED",
        "policy_version": policy.policy_version,
        "principle": policy.principle,
        "reuse_order_count": len(policy.reuse_order),
        "required_assessment_section_count": len(
            policy.required_assessment_sections
        ),
        "required_custom_build_evidence_count": len(
            policy.required_custom_build_evidence
        ),
        "custom_implementation_default_allowed": (
            policy.custom_implementation_default_allowed
        ),
        "unknown_license_reuse_allowed": (
            policy.unknown_license_reuse_allowed
        ),
        "copy_without_provenance_allowed": (
            policy.copy_without_provenance_allowed
        ),
        "vendor_sdk_reimplementation_allowed": (
            policy.vendor_sdk_reimplementation_allowed
        ),
        "network_connection_attempted": False,
        "database_connection_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
