# 本脚本核心功能：验证任务020a通用适配器合同的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.provider_capabilities import (
    load_provider_capability_matrix,
    load_single_machine_resource_profile,
)


# 配置常量：集中定义 `AUTHORITY_MARKERS`，供后续流程复用。
# - 当前值或构造表达式：`{'PROJECT_MEMORY.md': '<!-- TASK_020A_UNIVERSAL_ADAPTER_MEMORY -->', 'SYSTEM_ARCHITECTU...`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
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


# 函数 `require`：完成强制校验相关处理。
# - 输入：condition、message。
# - 处理：完成强制校验相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def require(condition: bool, message: str) -> None:
    # 条件分支：检查 `not condition` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not condition:
        # 失败门禁：抛出 `RuntimeError(message)`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise RuntimeError(message)


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 循环处理：将 `AUTHORITY_MARKERS.items()` 中的元素逐项绑定到 `(relative_path, marker)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
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
    # 输出结果：返回 `0` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
