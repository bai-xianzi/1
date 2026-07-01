# 本脚本核心功能：验证任务020b复用优先补充合同的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.reuse_first_policy import (
    load_reuse_first_policy,
)


# 配置常量：集中定义 `AUTHORITY_MARKERS`，供后续流程复用。
# - 当前值或构造表达式：`{'PROJECT_MEMORY.md': '<!-- TASK_020B_REUSE_MEMORY -->', 'SYSTEM_ARCHITECTURE.md': '<!-...`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
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
    # 循环处理：将 `AUTHORITY_MARKERS.items()` 中的元素逐项绑定到 `(relative_path, marker)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
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
