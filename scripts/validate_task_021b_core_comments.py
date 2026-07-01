# 本脚本核心功能：用跨Python版本稳定的完整目标源码摘要验证TASK_021B注释迁移成果。
# - 不再持久化Python内部数字Token编号。
# - read_text统一换行后计算目标源码SHA256。
# - 继续检查注释数量、统一教学式审计和Git阻断状态。
# - 为什么这样写：消除不同Python版本造成的批量误报，同时不降低业务源码完整性检查。
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


# 函数 `normalized_source_sha256`：完成 `scripts/validate_task_021b_core_comments.py` 中对应的独立处理步骤。
# - 输入：path。
# - 处理：保持原参数、控制流、API调用和异常语义，仅在定义前补充教学式说明。
# - 输出：返回原函数约定的对象、状态或退出结果，不改变数据形状和单位。
# - 为什么这样写：将输入、处理和输出固定为可审查合同，便于定位问题并防止注释迁移改变业务行为。
def normalized_source_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# 函数 `load_audit_module`：完成 `scripts/validate_task_021b_core_comments.py` 中对应的独立处理步骤。
# - 输入：path。
# - 处理：保持原参数、控制流、API调用和异常语义，仅在定义前补充教学式说明。
# - 输出：返回原函数约定的对象、状态或退出结果，不改变数据形状和单位。
# - 为什么这样写：将输入、处理和输出固定为可审查合同，便于定位问题并防止注释迁移改变业务行为。
def load_audit_module(path: Path):
    spec = importlib.util.spec_from_file_location("task_021b_portable_target_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载教学式注释审计器。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# 函数 `require`：完成 `scripts/validate_task_021b_core_comments.py` 中对应的独立处理步骤。
# - 输入：condition、message。
# - 处理：保持原参数、控制流、API调用和异常语义，仅在定义前补充教学式说明。
# - 输出：返回原函数约定的对象、状态或退出结果，不改变数据形状和单位。
# - 为什么这样写：将输入、处理和输出固定为可审查合同，便于定位问题并防止注释迁移改变业务行为。
def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


# 函数 `main`：完成 `scripts/validate_task_021b_core_comments.py` 中对应的独立处理步骤。
# - 输入：对象状态、模块配置或当前运行上下文。
# - 处理：保持原参数、控制流、API调用和异常语义，仅在定义前补充教学式说明。
# - 输出：返回原函数约定的对象、状态或退出结果，不改变数据形状和单位。
# - 为什么这样写：将输入、处理和输出固定为可审查合同，便于定位问题并防止注释迁移改变业务行为。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report = json.loads((root / "reports" / "task_021b_core_contracts_comment_migration.json").read_text(encoding="utf-8"))
    audit = load_audit_module(root / "scripts" / "audit_teaching_comments.py")

    require(report["task_id"] == "TASK_021B", "task_id异常。")
    require(report["target_file_count"] == 10, "目标文件数量异常。")
    require(report["semantic_verification_method"] == "ANNOTATED_TARGET_SOURCE_SHA256_V1", "便携验证方法异常。")
    require(report["target_source_identity_required"] is True, "目标源码一致性必须启用。")
    require(report["historical_source_to_target_semantic_identity_preserved"] is True, "缺少原迁移语义一致性历史证据。")
    require(report["business_logic_changed"] is False, "报告错误声明业务逻辑变化。")
    require(report["github_commit_allowed"] is False, "迁移中不得允许Git提交。")
    require(report["github_push_allowed"] is False, "迁移中不得允许GitHub推送。")

    violations: dict[str, list[str]] = {}
    for item in report["files"]:
        relative = item["path"]
        path = root / relative
        require(path.exists(), f"缺少迁移文件：{relative}")
        require(
            normalized_source_sha256(path) == item["normalized_target_source_sha256"],
            f"注释后目标源码发生变化：{relative}",
        )
        comments = sum(line.lstrip().startswith("#") for line in path.read_text(encoding="utf-8").splitlines())
        require(comments == item["after_comment_line_count"], f"注释行数量异常：{relative}")
        result = audit.audit_python_file(root, path)
        if result.violations:
            violations[relative] = list(result.violations)

    require(not violations, "TASK_021B仍有注释违规：" + json.dumps(violations, ensure_ascii=False))
    print(json.dumps({
        "task_id": "TASK_021B",
        "verification_hotfix": "TASK_021D2",
        "overall_status": "PASSED",
        "target_file_count": report["target_file_count"],
        "verification_method": report["semantic_verification_method"],
        "target_source_identity": True,
        "historical_source_to_target_semantic_identity_preserved": True,
        "business_logic_changed": False,
        "github_commit_allowed": False,
        "github_push_allowed": False
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
