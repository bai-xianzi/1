# 本文件核心功能：验证TASK_024D的Windows凭据后端、权威合同、Schema、测试和本地真实验收报告是否完整且不含秘密材料。
# - 输入：仓库根目录中的TASK_024D交付文件，以及可选的`--require-real-acceptance`关闭门禁。
# - 处理：检查文件、源码关键安全合同、JSON Schema和Windows真实报告；只读取文本和JSON，不访问Credential Manager。
# - 输出：通过时打印稳定完成标志，失败时逐项列出错误并返回非零退出码。
# - 常量依据：文件范围、引用格式、零网络/零数据库/零交易和真实验收布尔值来自TASK_024D权威合同。
# - 为什么这样写：高风险秘密基础设施不能只凭测试数量宣称完成，需要独立验证器阻断漏文件、明文回退和虚假验收报告。
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 本段代码核心功能：集中声明TASK_024D必须存在的代码、测试、合同、Schema和报告文件。
# - 输入：无运行时输入，路径与本任务交付范围一一对应。
# - 处理：后续验证函数逐项检查存在性和内容。
# - 输出：形成单一、可审计的文件验收基线。
# - 为什么这样写：多文件修改包最容易遗漏脚本或报告，集中清单能在提交前阻断不完整交付。
REQUIRED_FILES = (
    "src/a_stock_quant/windows_credential_store.py",
    "tests/test_windows_credential_store.py",
    "scripts/run_task_024d_windows_credential_store_acceptance.py",
    "schemas/windows_credential_reference_v1.schema.json",
    "WINDOWS_CREDENTIAL_STORE.md",
    "tasks/TASK_024D_WINDOWS_CREDENTIAL_REFERENCE_BACKEND.md",
    "reports/task_024d_windows_credential_store_acceptance.md",
)

REAL_ACCEPTANCE_REPORT = "reports/task_024d_windows_credential_store_real_acceptance.json"
EXPECTED_REFERENCE_PATTERN = (
    r"^windows-credential://WJX/provider/"
    r"[a-z][a-z0-9_]{1,63}/"
    r"[a-z][a-z0-9_]{1,63}/"
    r"[a-z][a-z0-9_]{1,63}$"
)

# 本段代码核心功能：声明源码和权威合同必须保留的安全设计标记。
# - 输入：文件相对路径与该文件必须包含的关键文本。
# - 处理：验证器按UTF-8读取并逐项执行子串检查。
# - 输出：任何关键合同回退都会形成明确错误。
# - 为什么这样写：文件存在不代表安全实现仍在，关键标记能防止后续误删命名空间、官方API、失败关闭或B2C无秘密状态。
REQUIRED_PHRASES = {
    "src/a_stock_quant/windows_credential_store.py": (
        "class WindowsCredentialStore",
        "class WinCredentialApi(Protocol)",
        "CredWriteW",
        "CredReadW",
        "CredDeleteW",
        "CredFree",
        'REFERENCE_SCHEME = "windows-credential"',
        'REFERENCE_AUTHORITY = "WJX"',
        "CRED_MAX_CREDENTIAL_BLOB_SIZE = 5 * 512",
        "def store_secret(",
        "def resolve_secret(",
        "def delete_secret(",
        '"secret_value": None',
    ),
    "tests/test_windows_credential_store.py": (
        "class InMemoryWinCredentialApi",
        "class WindowsCredentialStoreTests",
        "test_reference_parser_rejects_out_of_scope_targets",
        "test_default_ctypes_backend_fails_closed_off_windows",
    ),
    "scripts/run_task_024d_windows_credential_store_acceptance.py": (
        "submit_connection_form",
        "secrets.token_urlsafe",
        "store.resolve_secret(reference)",
        "store.delete_secret(reference)",
        '"secret_material_in_report": False',
    ),
    "WINDOWS_CREDENTIAL_STORE.md": (
        "B2C秘密输入",
        "CredWriteW / CredReadW / CredDeleteW / CredFree",
        "禁止自动降级到明文 JSON",
    ),
}

# 本段代码核心功能：声明源码中绝对不允许出现的明文持久化回退调用组合。
# - 输入：Windows凭据实现源码文本。
# - 处理：检查危险函数和典型秘密写文件模式；仅限制实现源码，不扫描说明文档中的禁止示例。
# - 输出：发现潜在明文文件写入或自制加密后端时形成错误。
# - 为什么这样写：TASK_024D明确要求失败关闭，任何JSON、普通文件或自制密码算法回退都必须经过新的权威审查而不能悄悄加入。
FORBIDDEN_SOURCE_PHRASES = (
    "open(secret",
    "write_text(secret",
    "write_bytes(secret",
    "json.dump(secret",
    "Fernet(",
    "AES.new(",
)


# 本段代码核心功能：从脚本位置向上查找包含PROJECT_MEMORY.md和src目录的仓库根目录。
# - 输入：当前验证脚本绝对路径。
# - 处理：依次检查当前目录和父目录的稳定仓库标志。
# - 输出：返回仓库根目录；无法定位时抛RuntimeError。
# - 常量依据：src/a_stock_quant和本任务权威合同WINDOWS_CREDENTIAL_STORE.md共同标识TASK_024D工作树。
# - 为什么这样写：脚本可以从仓库根目录、scripts目录或应用器中调用，减少用户路径错误。
def locate_repository_root() -> Path:
    script_path = Path(__file__).resolve()
    for candidate in (script_path.parent, *script_path.parents):
        if (
            (candidate / "src" / "a_stock_quant").is_dir()
            and (candidate / "WINDOWS_CREDENTIAL_STORE.md").is_file()
        ):
            return candidate
    raise RuntimeError("无法定位WJX仓库根目录。")


# 本段代码核心功能：验证必需文件存在且不是空文件。
# - 输入：仓库根目录和REQUIRED_FILES清单。
# - 处理：逐项检查文件类型和大小。
# - 输出：返回错误列表；空列表代表通过。
# - 为什么这样写：漏打文件时应在任何Windows秘密写入之前失败。
def validate_required_files(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"缺少文件：{relative_path}")
        elif path.stat().st_size == 0:
            errors.append(f"空文件：{relative_path}")
    return errors


# 本段代码核心功能：验证关键安全实现和权威说明仍包含任务要求的结构。
# - 输入：仓库根目录和REQUIRED_PHRASES映射。
# - 处理：读取UTF-8文本并逐项检查关键短语，同时扫描源码禁用回退模式。
# - 输出：返回内容缺失或危险实现错误列表。
# - 为什么这样写：高风险模块需要独立于单元测试的静态合同检查，防止测试被同步弱化后仍错误通过。
def validate_contract_content(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = root / relative_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{relative_path} 缺少关键内容：{phrase}")
    source_path = root / "src/a_stock_quant/windows_credential_store.py"
    if source_path.is_file():
        lowered = source_path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_SOURCE_PHRASES:
            if phrase.lower() in lowered:
                errors.append(f"凭据源码包含禁止的明文或自制加密回退：{phrase}")
    return errors


# 本段代码核心功能：验证Windows凭据安全状态JSON Schema的版本、标题、字段和引用正则。
# - 输入：仓库中的windows_credential_reference_v1.schema.json。
# - 处理：使用标准库解析JSON并核对2020-12、根对象、required、secret_value=null和reference pattern。
# - 输出：返回Schema格式或合同错误列表。
# - 常量依据：项目动态表单和TASK_025A统一采用JSON Schema 2020-12。
# - 为什么这样写：B2C前后端共享机器合同可以防止页面误把秘密原文作为可读字段返回。
def validate_schema(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "schemas/windows_credential_reference_v1.schema.json"
    if not path.is_file():
        return errors
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"凭据Schema无法解析：{exc}"]
    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("凭据Schema未使用JSON Schema 2020-12。")
    if payload.get("title") != "WJX Windows Credential Reference":
        errors.append("凭据Schema标题不匹配。")
    if payload.get("type") != "object" or payload.get("additionalProperties") is not False:
        errors.append("凭据Schema根对象必须拒绝额外字段。")
    required = payload.get("required")
    if set(required or ()) != {"backend", "reference", "configured", "secret_value"}:
        errors.append("凭据Schema required字段不匹配。")
    properties = payload.get("properties", {})
    if properties.get("reference", {}).get("pattern") != EXPECTED_REFERENCE_PATTERN:
        errors.append("凭据Schema引用正则不匹配。")
    if properties.get("secret_value", {}).get("type") != "null":
        errors.append("B2C凭据状态必须把secret_value限制为null。")
    return errors


# 本段代码核心功能：在正式关闭模式下验证Windows真实写入、读取、无泄漏和删除报告。
# - 输入：本地验收脚本生成的JSON文件和require_real_acceptance开关。
# - 处理：默认缺失仅跳过；关闭模式要求文件存在、状态通过、五项布尔门禁为真且副作用计数为零。
# - 输出：返回报告缺失、格式、泄漏或副作用错误列表。
# - 为什么这样写：Linux假后端测试不能替代用户Windows官方Credential Manager真实验收，关闭门禁必须读取当次报告。
def validate_real_acceptance(root: Path, *, required: bool) -> list[str]:
    errors: list[str] = []
    path = root / REAL_ACCEPTANCE_REPORT
    if not path.is_file():
        if required:
            errors.append(f"缺少Windows真实验收报告：{REAL_ACCEPTANCE_REPORT}")
        return errors
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Windows真实验收报告无法解析：{exc}"]
    expected_true = (
        "form_submission_verified",
        "safe_profile_verified",
        "round_trip_verified",
        "safe_status_verified",
        "deletion_verified",
    )
    if payload.get("task_id") != "TASK_024D" or payload.get("status") != "PASSED":
        errors.append("Windows真实验收报告任务或状态不匹配。")
    if payload.get("backend") != "WINDOWS_CREDENTIAL_MANAGER":
        errors.append("Windows真实验收报告后端不匹配。")
    for key in expected_true:
        if payload.get(key) is not True:
            errors.append(f"Windows真实验收门禁未通过：{key}")
    if payload.get("secret_material_in_report") is not False:
        errors.append("Windows真实验收报告未明确证明无秘密材料。")
    for key in ("network_requests", "database_write_operations", "trading_actions"):
        if payload.get(key) != 0:
            errors.append(f"Windows真实验收出现禁止副作用：{key}")
    reference = payload.get("reference")
    if not isinstance(reference, str) or not reference.startswith(
        "windows-credential://WJX/provider/wjx_probe/task_024d_probe/"
    ):
        errors.append("Windows真实验收引用不属于TASK_024D探针命名空间。")
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    forbidden_report_keys = ("secret_value", "credential_blob", "password", "api_key")
    lowered = serialized.lower()
    for key in forbidden_report_keys:
        if key in lowered:
            errors.append(f"Windows真实验收报告包含禁止秘密字段名：{key}")
    return errors


# 本段代码核心功能：解析命令行参数并允许应用器在Windows真实探针后提升验收强度。
# - 输入：可选`--require-real-acceptance`。
# - 处理：使用argparse生成布尔开关。
# - 输出：Namespace供main使用。
# - 为什么这样写：沙盒只能运行跨平台验证，用户本地提交前必须显式要求真实报告，两种环境共享一个验证器。
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate TASK_024D Windows credential backend artifacts."
    )
    parser.add_argument(
        "--require-real-acceptance",
        action="store_true",
        help="Require and validate the Windows real acceptance report.",
    )
    return parser.parse_args()


# 本段代码核心功能：汇总文件、合同、Schema和真实验收检查并返回可靠命令行退出码。
# - 输入：命令行开关和仓库当前文件。
# - 处理：顺序调用四类验证函数，集中输出错误。
# - 输出：通过返回0并打印PASSED标志；失败返回1。
# - 为什么这样写：PowerShell/Python应用器需要统一退出码阻断测试、提交和推送。
def main() -> int:
    args = parse_args()
    root = locate_repository_root()
    errors = [
        *validate_required_files(root),
        *validate_contract_content(root),
        *validate_schema(root),
        *validate_real_acceptance(root, required=args.require_real_acceptance),
    ]
    if errors:
        print("TASK_024D_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASK_024D_VALIDATION_PASSED")
    print(f"repository_root={root}")
    print(f"required_files={len(REQUIRED_FILES)}")
    print(f"real_acceptance_required={args.require_real_acceptance}")
    return 0


# 本段代码核心功能：仅在脚本作为命令行入口时运行验证流程。
# - 输入：Python提供的__name__标志。
# - 处理：调用main并把结果传给SystemExit。
# - 输出：向终端、应用器和CI提供稳定退出码。
# - 为什么这样写：测试或其他模块导入验证函数时不会自动扫描文件系统。
if __name__ == "__main__":
    sys.exit(main())
