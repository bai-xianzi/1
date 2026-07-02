# 本模块核心功能：在Windows主机上进行供应商无关的机器级Provider环境盘点。
# - 输入：TASK_023A Provider清单、Windows盘点规则、可注入的解释器/程序/环境快照。
# - 处理：发现多个Python解释器、仅用find_spec探测模块、读取卸载注册表中的程序名称。
# - 输出：不含密码、Token值和安装路径的TASK_023B候选排序报告。
# - 安全边界：不导入厂商SDK、不联网、不登录、不修改注册表、不写数据库、不启用交易。
"""TASK_023B Windows机器级Provider环境盘点。"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from a_stock_quant.provider_environment_discovery import ProviderTargetSpec


@dataclass(frozen=True)
class ProviderWindowsRule:
    """一个Provider的Windows本地证据匹配规则。"""

    provider_id: str
    installed_app_name_tokens: tuple[str, ...]
    executable_candidates: tuple[str, ...]


@dataclass(frozen=True)
class PythonInterpreterEvidence:
    """一个Python解释器及其离线模块发现结果。"""

    executable: str
    version: str
    source: str
    detected_modules: tuple[str, ...]
    probe_status: str


@dataclass(frozen=True)
class InstalledApplicationEvidence:
    """Windows卸载注册表中的安全程序元数据，不包含安装路径。"""

    display_name: str
    display_version: str
    publisher: str


@dataclass(frozen=True)
class ProviderWindowsFinding:
    """单一Provider的机器级证据、评分和下一步状态。"""

    provider_id: str
    display_name: str
    provider_kind: str
    execution_capability: bool
    priority: int
    evidence_score: int
    current_interpreter_modules: tuple[str, ...]
    other_interpreter_modules: tuple[str, ...]
    matched_installed_applications: tuple[str, ...]
    detected_executables: tuple[str, ...]
    present_credential_references: tuple[str, ...]
    inventory_status: str
    eligible_for_task_023c_review: bool
    blockers: tuple[str, ...]


def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        normalized.append(item.strip())
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(normalized)


def load_windows_inventory_rules(path: str | Path) -> tuple[ProviderWindowsRule, ...]:
    """读取TASK_023B规则，并强制保留零秘密值、零SDK导入和零网络边界。"""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    for field_name in (
        "secret_values_allowed",
        "vendor_sdk_import_allowed",
        "network_calls_allowed",
        "registry_install_location_allowed",
    ):
        if payload.get(field_name) is not False:
            raise ValueError(f"{field_name} must be false")

    raw_rules = payload.get("providers")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("providers must be a non-empty list")

    rules: list[ProviderWindowsRule] = []
    seen: set[str] = set()
    for raw in raw_rules:
        if not isinstance(raw, dict):
            raise ValueError("each provider rule must be an object")
        provider_id = raw.get("provider_id")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")
        provider_id = provider_id.strip()
        if provider_id in seen:
            raise ValueError(f"duplicate provider_id: {provider_id}")
        seen.add(provider_id)
        rules.append(
            ProviderWindowsRule(
                provider_id=provider_id,
                installed_app_name_tokens=_string_tuple(
                    raw.get("installed_app_name_tokens", []),
                    "installed_app_name_tokens",
                ),
                executable_candidates=_string_tuple(
                    raw.get("executable_candidates", []),
                    "executable_candidates",
                ),
            )
        )
    return tuple(rules)


def _dedupe_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """按Windows不区分大小写语义稳定去重解释器路径。"""

    result: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        value = str(raw).strip().strip('"')
        if not value:
            continue
        key = os.path.normcase(os.path.abspath(value))
        if key not in seen:
            seen.add(key)
            result.append(value)
    return tuple(result)


def discover_python_interpreter_paths() -> tuple[tuple[str, str], ...]:
    """只通过当前解释器、PATH和py启动器发现Python，不遍历磁盘。"""

    candidates: list[tuple[str, str]] = [(sys.executable, "CURRENT_INTERPRETER")]

    for executable_name in ("python", "python3"):
        located = shutil.which(executable_name)
        if located:
            candidates.append((located, f"PATH_{executable_name.upper()}"))

    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        candidates.append((str(Path(virtual_env) / "Scripts" / "python.exe"), "VIRTUAL_ENV"))

    py_launcher = shutil.which("py")
    if py_launcher and platform.system() == "Windows":
        try:
            completed = subprocess.run(
                [py_launcher, "-0p"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            for line in completed.stdout.splitlines():
                cleaned = line.strip()
                if not cleaned:
                    continue
                match = re.search(
                    r"([A-Za-z]:\\.*?python(?:w)?\.exe)\s*$",
                    cleaned,
                    flags=re.IGNORECASE,
                )
                if match:
                    candidates.append((match.group(1), "PY_LAUNCHER"))
        except (OSError, subprocess.SubprocessError):
            pass

    unique_paths = _dedupe_paths(path for path, _ in candidates)
    source_by_key = {
        os.path.normcase(os.path.abspath(path)): source for path, source in candidates
    }
    return tuple(
        (path, source_by_key[os.path.normcase(os.path.abspath(path))])
        for path in unique_paths
        if Path(path).is_file()
    )


def probe_python_interpreter(
    executable: str,
    source: str,
    module_names: Sequence[str],
) -> PythonInterpreterEvidence:
    """在目标解释器中调用find_spec；不会import任何待探测模块。"""

    probe_code = (
        "import importlib.util,json,platform,sys;"
        "mods=json.loads(sys.argv[1]);"
        "found=[];"
        "[(found.append(m) if importlib.util.find_spec(m) is not None else None) for m in mods];"
        "print(json.dumps({'version':platform.python_version(),'found':found},ensure_ascii=True))"
    )
    try:
        completed = subprocess.run(
            [executable, "-I", "-c", probe_code, json.dumps(list(module_names))],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        if completed.returncode != 0:
            return PythonInterpreterEvidence(executable, "", source, (), "PROBE_FAILED")
        payload = json.loads(completed.stdout.strip())
        found = tuple(str(item) for item in payload.get("found", []))
        return PythonInterpreterEvidence(
            executable=executable,
            version=str(payload.get("version", "")),
            source=source,
            detected_modules=found,
            probe_status="PASSED",
        )
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError):
        return PythonInterpreterEvidence(executable, "", source, (), "PROBE_FAILED")


def collect_python_interpreter_evidence(
    module_names: Sequence[str],
) -> tuple[PythonInterpreterEvidence, ...]:
    """对所有安全发现的解释器运行统一离线模块探测。"""

    return tuple(
        probe_python_interpreter(executable, source, module_names)
        for executable, source in discover_python_interpreter_paths()
    )


def collect_installed_applications() -> tuple[InstalledApplicationEvidence, ...]:
    """读取Windows卸载注册表，只保留名称、版本和发布者。"""

    if platform.system() != "Windows":
        return ()
    try:
        import winreg
    except ImportError:
        return ()

    roots = (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER)
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    access_modes = (winreg.KEY_READ, winreg.KEY_READ | getattr(winreg, "KEY_WOW64_32KEY", 0), winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0))
    records: dict[tuple[str, str, str], InstalledApplicationEvidence] = {}

    for root in roots:
        for access in access_modes:
            try:
                with winreg.OpenKey(root, subkey, 0, access) as uninstall_key:
                    index = 0
                    while True:
                        try:
                            child_name = winreg.EnumKey(uninstall_key, index)
                        except OSError:
                            break
                        index += 1
                        try:
                            with winreg.OpenKey(uninstall_key, child_name, 0, access) as child:
                                def read_value(name: str) -> str:
                                    try:
                                        value, _ = winreg.QueryValueEx(child, name)
                                        return str(value).strip()
                                    except OSError:
                                        return ""

                                display_name = read_value("DisplayName")
                                if not display_name:
                                    continue
                                record = InstalledApplicationEvidence(
                                    display_name=display_name,
                                    display_version=read_value("DisplayVersion"),
                                    publisher=read_value("Publisher"),
                                )
                                records[(record.display_name, record.display_version, record.publisher)] = record
                        except OSError:
                            continue
            except OSError:
                continue
    return tuple(sorted(records.values(), key=lambda item: item.display_name.casefold()))


def _matches_any_token(value: str, tokens: Sequence[str]) -> bool:
    normalized = value.casefold()
    return any(token.casefold() in normalized for token in tokens)


def build_windows_provider_findings(
    targets: Sequence[ProviderTargetSpec],
    rules: Sequence[ProviderWindowsRule],
    interpreters: Sequence[PythonInterpreterEvidence],
    applications: Sequence[InstalledApplicationEvidence],
    *,
    environ: Mapping[str, str] | None = None,
    executable_lookup: Callable[[str], str | None] | None = None,
) -> tuple[ProviderWindowsFinding, ...]:
    """把机器级事实映射为Provider证据评分；评分只用于决定23C评审顺序。"""

    environment = os.environ if environ is None else environ
    lookup = shutil.which if executable_lookup is None else executable_lookup
    rule_by_provider = {rule.provider_id: rule for rule in rules}
    current_key = os.path.normcase(os.path.abspath(sys.executable))
    findings: list[ProviderWindowsFinding] = []

    for target in targets:
        rule = rule_by_provider.get(target.provider_id)
        if rule is None:
            raise ValueError(f"missing Windows inventory rule: {target.provider_id}")

        current_modules: set[str] = set()
        other_modules: set[str] = set()
        for interpreter in interpreters:
            matched = set(interpreter.detected_modules).intersection(target.python_module_candidates)
            interpreter_key = os.path.normcase(os.path.abspath(interpreter.executable))
            if interpreter_key == current_key:
                current_modules.update(matched)
            else:
                other_modules.update(matched)

        matched_apps = tuple(
            app.display_name
            for app in applications
            if _matches_any_token(app.display_name, rule.installed_app_name_tokens)
        )
        detected_executables = tuple(
            name for name in rule.executable_candidates if lookup(name)
        )
        present_references = tuple(
            name for name in target.credential_reference_names if bool(environment.get(name))
        )

        score = 100 if current_modules else 0
        score += 80 if other_modules else 0
        score += 40 if matched_apps else 0
        score += 30 if detected_executables else 0
        score += 10 if present_references else 0

        blockers: list[str] = []
        if target.license_review_required:
            blockers.append("LICENSE_AND_AUTHORIZATION_REVIEW_REQUIRED")
        if target.execution_capability:
            blockers.append("EXECUTION_CAPABILITY_SEPARATE_ACTIVATION_REQUIRED")
        if score == 0:
            blockers.append("NO_LOCAL_PROVIDER_EVIDENCE")

        eligible = score > 0 and not target.execution_capability
        if target.execution_capability:
            inventory_status = "SEPARATE_EXECUTION_REVIEW_REQUIRED"
        elif eligible:
            inventory_status = "LOCAL_EVIDENCE_FOUND_TASK_023C_REVIEW_REQUIRED"
        else:
            inventory_status = "LOCAL_EVIDENCE_NOT_FOUND"

        findings.append(
            ProviderWindowsFinding(
                provider_id=target.provider_id,
                display_name=target.display_name,
                provider_kind=target.provider_kind,
                execution_capability=target.execution_capability,
                priority=target.priority,
                evidence_score=score,
                current_interpreter_modules=tuple(sorted(current_modules)),
                other_interpreter_modules=tuple(sorted(other_modules)),
                matched_installed_applications=tuple(sorted(set(matched_apps))),
                detected_executables=tuple(sorted(detected_executables)),
                present_credential_references=present_references,
                inventory_status=inventory_status,
                eligible_for_task_023c_review=eligible,
                blockers=tuple(blockers),
            )
        )
    return tuple(findings)


def rank_task_023c_candidates(
    findings: Iterable[ProviderWindowsFinding],
) -> tuple[str, ...]:
    """按证据分降序、业务优先级升序和provider_id稳定排序。"""

    candidates = [item for item in findings if item.eligible_for_task_023c_review]
    candidates.sort(key=lambda item: (-item.evidence_score, item.priority, item.provider_id))
    return tuple(item.provider_id for item in candidates)


def build_windows_inventory_report(
    findings: Sequence[ProviderWindowsFinding],
    interpreters: Sequence[PythonInterpreterEvidence],
    applications: Sequence[InstalledApplicationEvidence],
) -> dict[str, object]:
    """生成可供TASK_023C读取的安全报告，不把秘密值和安装路径写入文件。"""

    ranked = rank_task_023c_candidates(findings)
    return {
        "task_id": "TASK_023B",
        "mode": "WINDOWS_MACHINE_LEVEL_PROVIDER_INVENTORY",
        "overall_status": "PASSED_WITH_WARNINGS" if findings else "FAILED",
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "python_interpreter_count": len(interpreters),
        "installed_applications_scanned_count": len(applications),
        "provider_count": len(findings),
        "providers_with_local_evidence_count": sum(item.evidence_score > 0 for item in findings),
        "recommended_task_023c_provider_ids": list(ranked),
        "selection_status": "CANDIDATES_REQUIRE_MANUAL_REVIEW" if ranked else "NO_LOCAL_PROVIDER_EVIDENCE",
        "python_interpreters": [asdict(item) for item in interpreters],
        "findings": [asdict(item) for item in findings],
        "vendor_sdk_imports": 0,
        "network_calls": 0,
        "database_write_operations": 0,
        "registry_write_operations": 0,
        "secret_values_recorded": 0,
        "installation_paths_recorded": 0,
        "activation_performed": False,
    }


def write_windows_inventory_report(report: Mapping[str, object], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
