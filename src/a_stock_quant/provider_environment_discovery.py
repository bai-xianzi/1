# 本模块核心功能：在不导入供应商SDK、不联网、不读取秘密值的前提下，盘点外部Provider运行环境。
# - 输入：供应商发现清单、当前Python环境、可选环境变量名称和值、可注入的模块查找函数。
# - 处理：只检查模块是否可发现、凭据引用名称是否存在，并按安全规则生成候选排序。
# - 输出：可序列化的环境盘点报告；任何结果都不等于许可证通过、能力验证或正式激活。
# - 为什么这样写：把所有供应商共用的环境发现逻辑集中复用，避免为每一家SDK重复造轮子。
"""供应商无关的外部Provider环境发现工具。"""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence


# ProviderTargetSpec：表示发现清单中的一个外部Provider目标，不包含任何密码、Token或账户值。
@dataclass(frozen=True)
class ProviderTargetSpec:
    provider_id: str
    display_name: str
    provider_kind: str
    execution_capability: bool
    priority: int
    python_module_candidates: tuple[str, ...]
    credential_reference_names: tuple[str, ...]
    discovery_method: str
    evidence_level: str
    license_review_required: bool


# ProviderEnvironmentFinding：记录单一Provider在当前环境中能被安全证明的事实。
@dataclass(frozen=True)
class ProviderEnvironmentFinding:
    provider_id: str
    display_name: str
    provider_kind: str
    execution_capability: bool
    priority: int
    runtime_status: str
    detected_python_modules: tuple[str, ...]
    present_credential_references: tuple[str, ...]
    discovery_method: str
    evidence_level: str
    license_review_required: bool
    eligible_for_next_discovery: bool
    blockers: tuple[str, ...]


# _require_non_empty_string：统一校验外部JSON中的身份字段，避免空字符串进入报告和排序。
def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


# _require_string_tuple：把JSON字符串数组转换为不可变元组，并拒绝重复项和非字符串值。
def _require_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized = tuple(_require_non_empty_string(item, field_name) for item in value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return normalized


# load_provider_discovery_manifest：读取并强校验TASK_023A发现清单。
# - 输入：JSON文件路径。
# - 输出：按配置顺序返回ProviderTargetSpec元组。
# - 安全约束：清单不得允许秘密值、SDK导入或网络调用。
def load_provider_discovery_manifest(path: str | Path) -> tuple[ProviderTargetSpec, ...]:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    if payload.get("secret_values_allowed") is not False:
        raise ValueError("secret_values_allowed must be false")
    if payload.get("vendor_sdk_import_allowed") is not False:
        raise ValueError("vendor_sdk_import_allowed must be false")
    if payload.get("network_calls_allowed") is not False:
        raise ValueError("network_calls_allowed must be false")

    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ValueError("targets must be a non-empty list")

    targets: list[ProviderTargetSpec] = []
    seen_provider_ids: set[str] = set()
    for raw in raw_targets:
        if not isinstance(raw, dict):
            raise ValueError("each target must be an object")
        provider_id = _require_non_empty_string(raw.get("provider_id"), "provider_id")
        if provider_id in seen_provider_ids:
            raise ValueError(f"duplicate provider_id: {provider_id}")
        seen_provider_ids.add(provider_id)

        priority = raw.get("priority")
        if not isinstance(priority, int) or priority < 0:
            raise ValueError(f"priority must be a non-negative integer: {provider_id}")

        targets.append(
            ProviderTargetSpec(
                provider_id=provider_id,
                display_name=_require_non_empty_string(raw.get("display_name"), "display_name"),
                provider_kind=_require_non_empty_string(raw.get("provider_kind"), "provider_kind"),
                execution_capability=bool(raw.get("execution_capability", False)),
                priority=priority,
                python_module_candidates=_require_string_tuple(
                    raw.get("python_module_candidates", []), "python_module_candidates"
                ),
                credential_reference_names=_require_string_tuple(
                    raw.get("credential_reference_names", []), "credential_reference_names"
                ),
                discovery_method=_require_non_empty_string(
                    raw.get("discovery_method"), "discovery_method"
                ),
                evidence_level=_require_non_empty_string(raw.get("evidence_level"), "evidence_level"),
                license_review_required=bool(raw.get("license_review_required", True)),
            )
        )
    return tuple(targets)


# _module_is_discoverable：只调用find_spec判断模块入口是否存在，不执行import，也不触发SDK登录。
def _module_is_discoverable(
    module_name: str,
    find_spec: Callable[[str], object | None],
) -> bool:
    try:
        return find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False


# discover_provider_environment：对全部目标执行离线环境发现并生成逐Provider事实。
# - environ只用于判断配置中列出的引用名称是否存在；报告绝不保存对应值。
# - execution_capability为真的Provider即使检测到运行时，也不能成为自动推荐的数据接入候选。
def discover_provider_environment(
    targets: Sequence[ProviderTargetSpec],
    *,
    environ: Mapping[str, str] | None = None,
    find_spec: Callable[[str], object | None] | None = None,
) -> tuple[ProviderEnvironmentFinding, ...]:
    environment = os.environ if environ is None else environ
    module_finder = importlib.util.find_spec if find_spec is None else find_spec
    findings: list[ProviderEnvironmentFinding] = []

    for target in targets:
        detected_modules = tuple(
            module_name
            for module_name in target.python_module_candidates
            if _module_is_discoverable(module_name, module_finder)
        )
        present_references = tuple(
            name
            for name in target.credential_reference_names
            if bool(environment.get(name))
        )

        blockers: list[str] = []
        if detected_modules:
            runtime_status = "RUNTIME_PRESENT"
        elif target.python_module_candidates:
            runtime_status = "RUNTIME_NOT_DETECTED"
            blockers.append("PYTHON_RUNTIME_NOT_DETECTED")
        else:
            runtime_status = "MANUAL_REVIEW_REQUIRED"
            blockers.append("NO_VERIFIED_PYTHON_MODULE_HINT")

        if target.license_review_required:
            blockers.append("LICENSE_REVIEW_REQUIRED")
        if target.execution_capability:
            blockers.append("EXECUTION_CAPABILITY_SEPARATE_ACTIVATION_REQUIRED")

        eligible = bool(detected_modules) and not target.execution_capability
        findings.append(
            ProviderEnvironmentFinding(
                provider_id=target.provider_id,
                display_name=target.display_name,
                provider_kind=target.provider_kind,
                execution_capability=target.execution_capability,
                priority=target.priority,
                runtime_status=runtime_status,
                detected_python_modules=detected_modules,
                present_credential_references=present_references,
                discovery_method=target.discovery_method,
                evidence_level=target.evidence_level,
                license_review_required=target.license_review_required,
                eligible_for_next_discovery=eligible,
                blockers=tuple(blockers),
            )
        )
    return tuple(findings)


# rank_next_discovery_candidates：只对已检测到运行时、且不具备交易执行能力的目标排序。
# - priority数值越小越优先；同优先级按provider_id稳定排序。
# - 排序结果只是下一步详细发现候选，不代表激活、许可通过或生产路由。
def rank_next_discovery_candidates(
    findings: Iterable[ProviderEnvironmentFinding],
) -> tuple[str, ...]:
    candidates = [finding for finding in findings if finding.eligible_for_next_discovery]
    candidates.sort(key=lambda finding: (finding.priority, finding.provider_id))
    return tuple(finding.provider_id for finding in candidates)


# build_provider_environment_report：组合环境元数据、逐Provider发现和候选顺序。
# - 报告显式记录零网络、零SDK导入、零数据库写入，便于验收安全边界。
def build_provider_environment_report(
    findings: Sequence[ProviderEnvironmentFinding],
) -> dict[str, object]:
    ranked_candidates = rank_next_discovery_candidates(findings)
    return {
        "task_id": "TASK_023A",
        "mode": "OFFLINE_PROVIDER_ENVIRONMENT_DISCOVERY",
        "overall_status": "PASSED_WITH_WARNINGS" if findings else "FAILED",
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "provider_count": len(findings),
        "runtime_present_count": sum(
            finding.runtime_status == "RUNTIME_PRESENT" for finding in findings
        ),
        "recommended_next_discovery_provider_ids": list(ranked_candidates),
        "selection_status": (
            "CANDIDATE_ONLY_NOT_ACTIVATED" if ranked_candidates else "NO_EXTERNAL_RUNTIME_DETECTED"
        ),
        "findings": [asdict(finding) for finding in findings],
        "vendor_sdk_imports": 0,
        "network_calls": 0,
        "database_write_operations": 0,
        "secret_values_recorded": 0,
    }


# write_provider_environment_report：以UTF-8和稳定缩进写出JSON，便于Git审查和后续任务读取。
def write_provider_environment_report(report: Mapping[str, object], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
