# 本文件核心功能：验证TASK_024E接入中心页面、后端、Schema、测试、文档和安全门禁是否完整落地。
# - 输入：当前仓库根目录中的本任务文件。
# - 处理：检查文件、关键合同、JSON Schema、页面安全约束、纯引用持久化和任务状态文案。
# - 输出：通过时打印TASK_024E_VALIDATION_PASSED，失败时逐条列出并返回非零退出码。
# - 常量依据：TASK_024E任务合同与B2C双视图权威文件。
# - 为什么这样写：多文件页面任务不能只依赖单元测试，静态合同验证可阻断漏包、文档未同步或安全语义回退。
"""Validate TASK_024E provider connection-center B2C delivery."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FILES = (
    "src/a_stock_quant/provider_connection_b2c.py",
    "src/a_stock_quant/provider_connection_page.py",
    "scripts/run_provider_connection_center.py",
    "scripts/validate_task_024e_provider_connection_b2c.py",
    "tests/test_provider_connection_b2c.py",
    "schemas/provider_connection_profile_store.schema.json",
    "tasks/TASK_024E_PROVIDER_CONNECTION_CENTER_B2C.md",
    "reports/task_024e_provider_connection_center_b2c_acceptance.md",
)

REQUIRED_SOURCE_PHRASES = {
    "src/a_stock_quant/provider_connection_b2c.py": (
        "class JsonProviderConnectionProfileRepository",
        "class ProviderConnectionCenterService",
        "class ProviderConnectionCenterWSGIApp",
        "READ_ONLY_TESTER_NOT_AVAILABLE",
        "parse_credential_reference",
        "action_availability",
    ),
    "src/a_stock_quant/provider_connection_page.py": (
        "这个页面是干什么的",
        "Windows安全凭据",
        "X-WJX-CSRF-Token",
        "交易能力：BLOCKED",
    ),
    "scripts/run_provider_connection_center.py": (
        "127.0.0.1",
        "testers={}",
        "TASK_024F",
    ),
}

PATCHED_DOC_PHRASES = {
    "PROVIDER_CONNECTION_CENTER.md": "TASK_024E：本地B2C页面与应用后端",
    "B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md": "数据接口接入中心纵向样板已实现",
    "SYSTEM_ARCHITECTURE.md": "TASK_024E完成：接入中心B2C纵向样板",
    "PROJECT_STATUS.md": "TASK_024E：数据接口接入中心页面与后端接口",
}


# 本段代码核心功能：向上定位包含PROJECT_MEMORY.md的仓库根目录。
# - 输入：当前验证脚本路径。
# - 处理：依次检查父目录。
# - 输出：仓库根Path或RuntimeError。
# - 为什么这样写：支持从仓库根、scripts目录和应用器中运行同一验证入口。
def locate_repository_root() -> Path:
    script = Path(__file__).resolve()
    for candidate in script.parents:
        if (candidate / "PROJECT_MEMORY.md").is_file():
            return candidate
    raise RuntimeError("Cannot locate WJX repository root.")


# 本段代码核心功能：检查本任务所有文件存在且非空。
# - 输入：仓库根和REQUIRED_FILES。
# - 处理：逐项检查is_file和size。
# - 输出：错误列表。
# - 为什么这样写：阻止ZIP漏文件或复制路径错误。
def validate_files(root: Path) -> list[str]:
    errors = []
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing file: {relative}")
        elif path.stat().st_size == 0:
            errors.append(f"empty file: {relative}")
    return errors


# 本段代码核心功能：检查源码与权威文档包含核心安全和阶段边界。
# - 输入：源码短语和应用器追加的文档标记。
# - 处理：UTF-8读取并逐项查找。
# - 输出：缺失内容错误列表。
# - 为什么这样写：文件存在不代表实现了本地限制、CSRF、测试器边界和权威同步。
def validate_content(root: Path) -> list[str]:
    errors = []
    for relative, phrases in REQUIRED_SOURCE_PHRASES.items():
        text = (root / relative).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{relative} missing phrase: {phrase}")
    for relative, phrase in PATCHED_DOC_PHRASES.items():
        path = root / relative
        if not path.is_file() or phrase not in path.read_text(encoding="utf-8"):
            errors.append(f"{relative} missing TASK_024E authority marker")
    return errors


# 本段代码核心功能：解析档案JSON Schema并检查秘密只允许凭据引用。
# - 输入：provider_connection_profile_store.schema.json。
# - 处理：标准库解析并核对方言、版本、additionalProperties和引用正则。
# - 输出：Schema错误列表。
# - 为什么这样写：无秘密档案是页面和Windows保险箱之间的机器边界，必须由可验证合同约束。
def validate_schema(root: Path) -> list[str]:
    errors = []
    path = root / "schemas/provider_connection_profile_store.schema.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"schema parse failed: {exc}"]
    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("schema dialect mismatch")
    if payload.get("additionalProperties") is not False:
        errors.append("profile store root must reject additional properties")
    profiles = payload.get("properties", {}).get("profiles", {}).get("items", {})
    if profiles.get("additionalProperties") is not False:
        errors.append("profile entries must reject additional properties")
    reference = profiles.get("properties", {}).get("credential_references", {}).get("additionalProperties", {})
    if reference.get("pattern") != "^windows-credential://WJX/provider/":
        errors.append("credential reference pattern mismatch")
    return errors


# 本段代码核心功能：静态检查页面不使用浏览器持久化、外部脚本或明文秘密回填。
# - 输入：provider_connection_page.py文本。
# - 处理：检查危险调用和安全控件语义。
# - 输出：安全回退错误列表。
# - 为什么这样写：页面处理密钥，任何localStorage、外链脚本或value回填都可能扩大泄露面。
def validate_page_security(root: Path) -> list[str]:
    text = (root / "src/a_stock_quant/provider_connection_page.py").read_text(encoding="utf-8")
    errors = []
    for forbidden in ("localStorage.", "sessionStorage.", "<script src=", "innerHTML ="):
        if forbidden in text:
            errors.append(f"page contains forbidden construct: {forbidden}")
    if "input.type = spec['x-field-kind'] === 'secret' ? 'password' : 'text'" not in text:
        errors.append("secret input is not rendered as password")
    if "input.value = payload.profile?.public_configuration?.[fieldId]" not in text:
        errors.append("public configuration refill path missing")
    return errors


# 本段代码核心功能：汇总验证并提供自动化可用退出码。
# - 输入：四类验证错误。
# - 处理：合并、输出并返回0或1。
# - 输出：TASK_024E_VALIDATION_PASSED或FAILED。
# - 为什么这样写：应用器必须在Git提交前获得单一明确门禁。
def main() -> int:
    root = locate_repository_root()
    errors = [
        *validate_files(root),
        *validate_content(root),
        *validate_schema(root),
        *validate_page_security(root),
    ]
    if errors:
        print("TASK_024E_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASK_024E_VALIDATION_PASSED")
    print(f"repository_root={root}")
    print(f"validated_files={len(REQUIRED_FILES)}")
    return 0


# 本段代码核心功能：命令行直接执行时返回可靠退出码。
# - 输入：Python运行标志。
# - 处理：调用main。
# - 输出：供PowerShell和CI判断成功或失败。
# - 为什么这样写：导入函数测试时不会自动扫描仓库。
if __name__ == "__main__":
    sys.exit(main())
