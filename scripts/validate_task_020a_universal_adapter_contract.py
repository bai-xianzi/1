from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.provider_capabilities import (
    load_provider_capability_matrix,
    load_single_machine_resource_profile,
)


AUTHORITY_MARKERS = {
    "PROJECT_MEMORY.md": "<!-- TASK_020A_UNIVERSAL_ADAPTER_MEMORY -->",
    "SYSTEM_ARCHITECTURE.md": (
        "<!-- TASK_020A_UNIVERSAL_ADAPTER_ARCHITECTURE -->"
    ),
    "DEVELOPMENT_GUIDANCE.md": (
        "<!-- TASK_020A_UNIVERSAL_ADAPTER_GUIDANCE -->"
    ),
    "INSTITUTIONAL_RESEARCH_AND_EXECUTION_GOVERNANCE.md": (
        "<!-- TASK_020A_UNIVERSAL_ADAPTER_GOVERNANCE -->"
    ),
    "AGENTS.md": "<!-- TASK_020A_UNIVERSAL_ADAPTER_AGENTS -->",
    "PROJECT_STATUS.md": "<!-- TASK_020A_STATUS -->",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    matrix = load_provider_capability_matrix(
        root
        / "configs"
        / "providers"
        / "provider_capability_matrix_v0.json"
    )
    profile = load_single_machine_resource_profile(
        root
        / "configs"
        / "runtime"
        / "windows_single_machine_resource_profile_v0.json"
    )

    require(
        (root / "MULTI_SOURCE_ADAPTER_ARCHITECTURE.md").exists(),
        "缺少多源适配架构权威文件",
    )
    for relative_path, marker in AUTHORITY_MARKERS.items():
        path = root / relative_path
        require(path.exists(), f"缺少权威文件：{relative_path}")
        require(
            marker in path.read_text(encoding="utf-8"),
            f"{relative_path}缺少TASK_020A权威标记",
        )

    required_provider_ids = {
        "local_dolphindb",
        "wind",
        "ifind",
        "galaxy_xingyao",
        "qmt",
        "ptrade",
    }
    provider_ids = {
        item.provider_id for item in matrix.provider_targets
    }
    require(
        required_provider_ids.issubset(provider_ids),
        "强制Provider目标不完整",
    )
    require(
        len(matrix.required_adapter_contracts) >= 10,
        "适配器合同维度不足",
    )
    require(
        len(matrix.capability_catalog) >= 18,
        "标准能力目录不足",
    )
    require(
        profile.max_parallel_provider_calls <= 2,
        "Provider并发不符合当前单机",
    )
    require(
        profile.max_parallel_cpu_jobs <= 2,
        "CPU并发不符合当前单机",
    )
    require(
        profile.maximum_batch_rows_without_override == 100000,
        "无人工覆盖批次上限异常",
    )
    require(
        not profile.automatic_35gb_minute_data_import_allowed,
        "错误允许自动导入35GB分钟线",
    )
    require(
        not profile.gpu_enabled_by_default,
        "GPU被错误默认启用",
    )

    output = {
        "task_id": "TASK_020A",
        "overall_status": "PASSED",
        "matrix_version": matrix.matrix_version,
        "provider_target_count": len(matrix.provider_targets),
        "capability_catalog_count": len(matrix.capability_catalog),
        "required_adapter_contract_count": len(
            matrix.required_adapter_contracts
        ),
        "required_provider_targets_present": True,
        "provider_neutral": matrix.provider_neutral,
        "automatic_activation_allowed": (
            matrix.automatic_activation_allowed
        ),
        "secret_storage_allowed": matrix.secret_storage_allowed,
        "machine_profile": profile.profile_id,
        "memory_gib": profile.memory_gib,
        "max_parallel_provider_calls": (
            profile.max_parallel_provider_calls
        ),
        "max_parallel_cpu_jobs": profile.max_parallel_cpu_jobs,
        "default_batch_rows": profile.default_batch_rows,
        "maximum_batch_rows_without_override": (
            profile.maximum_batch_rows_without_override
        ),
        "automatic_35gb_minute_data_import_allowed": (
            profile.automatic_35gb_minute_data_import_allowed
        ),
        "gpu_enabled_by_default": profile.gpu_enabled_by_default,
        "database_connection_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
