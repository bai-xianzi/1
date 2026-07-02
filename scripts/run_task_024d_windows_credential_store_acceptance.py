# 本文件核心功能：在用户Windows真实环境中验收接入中心秘密提交到Credential Manager的完整写入、读取、白箱状态和删除闭环。
# - 输入：Windows当前用户凭据集、TASK_024C表单合同和本任务WindowsCredentialStore实现。
# - 处理：生成一次性随机秘密，通过submit_connection_form保存引用，按引用读取验证，再删除并确认不存在。
# - 输出：不含秘密原文的JSON验收报告；任何步骤失败都返回非零退出码，并在finally中尽力清理探针凭据。
# - 常量依据：探针Provider、连接和字段标识只用于TASK_024D，不连接真实券商、不请求网络、不写DolphinDB。
# - 为什么这样写：单元测试只能验证假后端，正式关闭TASK_024D必须证明用户Windows账户的官方Credential Manager真实可用。
from __future__ import annotations

import argparse
import json
import platform
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

# 本段代码核心功能：把仓库src目录加入当前脚本导入路径。
# - 输入：脚本文件绝对路径。
# - 处理：定位仓库根目录并把src插入sys.path首位。
# - 输出：始终导入当前工作树中的接入中心和Windows凭据实现。
# - 为什么这样写：避免用户机器中已安装的旧包遮蔽本次待验收代码。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.provider_connection_center import (  # noqa: E402
    ConnectionFieldDefinition,
    FieldKind,
    PersistMode,
    ProviderConnectionDefinition,
    profile_to_safe_dict,
    submit_connection_form,
)
from a_stock_quant.windows_credential_store import (  # noqa: E402
    CredentialNotFoundError,
    WindowsCredentialStore,
)

# 本段代码核心功能：声明不会与真实Provider记录冲突的TASK_024D探针标识。
# - 输入：无运行时输入。
# - 处理：作为接入中心定义、Windows目标名和最终报告的稳定标识。
# - 输出：仅创建`WJX/provider/wjx_probe/task_024d_probe/probe_secret`目标。
# - 常量依据：全部标识符合TASK_024C小写字母数字下划线规则，并明确包含probe语义。
# - 为什么这样写：验收不能触碰用户真实券商凭据，也不能依赖任何已授权SDK。
PROBE_PROVIDER_ID = "wjx_probe"
PROBE_CONNECTION_ID = "task_024d_probe"
PROBE_FIELD_ID = "probe_secret"


# 本段代码核心功能：创建只含一个秘密字段的最小Provider接入定义。
# - 输入：无外部数据。
# - 处理：使用TASK_024C正式领域对象声明SECRET和CREDENTIAL_REFERENCE。
# - 输出：可传给submit_connection_form的ProviderConnectionDefinition。
# - 为什么这样写：真实验收不仅测试底层WinCred，还证明B2C提交边界会立即把秘密交换成安全引用。
def build_probe_definition() -> ProviderConnectionDefinition:
    return ProviderConnectionDefinition(
        provider_id=PROBE_PROVIDER_ID,
        display_name="WJX TASK 024D Probe",
        provider_kind="LOCAL_SECURITY_PROBE",
        authority_tier="PROJECT_INTERNAL",
        official_application_reference="",
        form_definition_status="OFFICIAL_FIELDS_VERIFIED",
        supports_read_only_data=True,
        contains_execution_capability=False,
        fields=(
            ConnectionFieldDefinition(
                field_id=PROBE_FIELD_ID,
                label="One-time probe secret",
                kind=FieldKind.SECRET,
                required=True,
                persist_mode=PersistMode.CREDENTIAL_REFERENCE,
                help_text="Generated only for TASK_024D acceptance.",
            ),
        ),
    )


# 本段代码核心功能：执行一次真实Windows Credential Manager端到端探针并返回无秘密报告。
# - 输入：当前Windows用户会话和操作系统凭据集。
# - 处理：随机生成秘密、提交表单、验证安全档案、读取比对、构建安全状态、删除并确认缺失。
# - 输出：只包含布尔结果、后端和安全引用的字典。
# - 为什么这样写：随机值不落盘、不打印，finally删除保证正常或异常路径都尽量不留测试凭据。
def run_acceptance() -> dict[str, object]:
    if platform.system() != "Windows":
        raise RuntimeError("TASK_024D real acceptance must run on Windows")

    store = WindowsCredentialStore()
    definition = build_probe_definition()
    secret_value = secrets.token_urlsafe(48)
    reference: str | None = None
    deletion_verified = False

    try:
        profile = submit_connection_form(
            definition,
            connection_id=PROBE_CONNECTION_ID,
            submitted_values={PROBE_FIELD_ID: secret_value},
            official_authorization_confirmed=True,
            read_only_entitlement_confirmed=True,
            execution_domain_isolated=True,
            credential_writer=store,
        )
        reference = profile.credential_references[PROBE_FIELD_ID]
        safe_profile = profile_to_safe_dict(profile)
        serialized_profile = json.dumps(safe_profile, ensure_ascii=False, sort_keys=True)
        if secret_value in serialized_profile:
            raise RuntimeError("secret leaked into safe connection profile")
        if store.resolve_secret(reference) != secret_value:
            raise RuntimeError("Windows Credential Manager round trip mismatch")
        safe_status = store.build_safe_status(reference)
        if safe_status.get("configured") is not True:
            raise RuntimeError("safe credential status did not report configured")
        if secret_value in json.dumps(safe_status, ensure_ascii=False, sort_keys=True):
            raise RuntimeError("secret leaked into safe credential status")
        store.delete_secret(reference)
        deletion_verified = not store.secret_exists(reference)
        if not deletion_verified:
            raise RuntimeError("probe credential still exists after deletion")
        return {
            "task_id": "TASK_024D",
            "status": "PASSED",
            "tested_at_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "backend": "WINDOWS_CREDENTIAL_MANAGER",
            "reference": reference,
            "form_submission_verified": True,
            "safe_profile_verified": True,
            "round_trip_verified": True,
            "safe_status_verified": True,
            "deletion_verified": True,
            "secret_material_in_report": False,
            "network_requests": 0,
            "database_write_operations": 0,
            "trading_actions": 0,
        }
    finally:
        # 本段代码核心功能：异常路径尽力删除已经写入的探针凭据。
        # - 输入：可能已经生成的reference和deletion_verified状态。
        # - 处理：仅在尚未确认删除时调用delete_secret；不存在视为已经清理。
        # - 输出：不覆盖原始异常，不打印秘密。
        # - 为什么这样写：安全验收失败也不能把一次性秘密长期留在用户凭据集中。
        if reference is not None and not deletion_verified:
            try:
                store.delete_secret(reference)
            except CredentialNotFoundError:
                pass


# 本段代码核心功能：解析报告路径、运行真实验收并以UTF-8 JSON写入项目报告目录。
# - 输入：可选`--output`路径。
# - 处理：创建父目录，调用run_acceptance，序列化无秘密报告并打印简要结果。
# - 输出：JSON文件和成功退出码0；失败由异常产生非零退出码。
# - 为什么这样写：应用脚本可以把真实Windows证据纳入同一Git提交，后续用户和系统都能审计验收边界。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="reports/task_024d_windows_credential_store_real_acceptance.json",
    )
    args = parser.parse_args()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = run_acceptance()
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("TASK_024D_WINDOWS_CREDENTIAL_STORE_ACCEPTANCE_PASSED")
    print(f"report={output_path}")
    print(f"reference={report['reference']}")
    return 0


# 本段代码核心功能：仅在脚本作为命令行入口运行时执行真实Windows验收。
# - 输入：Python运行标志。
# - 处理：调用main并把返回值交给SystemExit。
# - 输出：供PowerShell应用器和用户终端读取的可靠退出码。
# - 为什么这样写：被测试导入时不会意外写入Windows凭据集。
if __name__ == "__main__":
    raise SystemExit(main())
