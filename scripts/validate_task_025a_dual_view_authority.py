from __future__ import annotations

import json
import sys
from pathlib import Path

# 本段代码核心功能：声明TASK_025A必须存在的权威文件、机器合同和关键设计短语。
# - 输入：常量来自本任务实际新增或修改的仓库相对路径。
# - 处理：后续验证函数按这些清单逐项读取和检查。
# - 输出：形成单一、可审计的任务验收基线。
# - 常量依据：文件名与B2C双视图、Skill平台及六个基础Schema的权威设计一一对应。
# - 为什么这样写：集中声明可防止验证脚本遗漏某个文件，并便于后续任务扩展验收范围。
REQUIRED_FILES = (
    "PROJECT_MEMORY.md",
    "SYSTEM_ARCHITECTURE.md",
    "DEVELOPMENT_GUIDANCE.md",
    "PROJECT_CONTEXT.md",
    "README_PROJECT_MEMORY.md",
    "START_HERE.md",
    "PROJECT_STATUS.md",
    "PROVIDER_CONNECTION_CENTER.md",
    "B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md",
    "SKILL_PLATFORM_ARCHITECTURE.md",
    "schemas/b2c_module_manifest.schema.json",
    "schemas/b2c_action_contract.schema.json",
    "schemas/explanation_trace.schema.json",
    "schemas/field_proposal.schema.json",
    "schemas/skill_definition.schema.json",
    "schemas/research_artifact.schema.json",
)

REQUIRED_PHRASES = {
    "PROJECT_MEMORY.md": (
        "产品设计总原则",
        "Skill 总原则",
        "双合同设计原则",
        "虚拟沙盒、本地环境与GitHub任务治理原则",
    ),
    "SYSTEM_ARCHITECTURE.md": (
        "V11双视图项目权威版",
        "用户端与系统内部双结构图",
        "B2C用户控制平面与白箱解释",
        "统一Skill平台",
    ),
    "DEVELOPMENT_GUIDANCE.md": (
        "从用户操作界面反向设计内部系统",
        "全系统 B2C 与 Skill 开发门禁",
        "B2C交互合同",
    ),
    "B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md": (
        "B2C 不是最后补上的前端",
        "B2CModuleManifest",
        "B2CActionContract",
        "ExplanationTrace",
        "FieldProposal",
    ),
    "SKILL_PLATFORM_ARCHITECTURE.md": (
        "开发型 Skill",
        "产品型 Skill",
        "ResearchArtifact",
        "人物知识与决策机制蒸馏",
        "CANDIDATE_FACTOR",
    ),
    "PROJECT_STATUS.md": (
        "TASK_025A：全系统B2C双视图与Skill平台权威架构",
        "TASK_024D",
    ),
}

SCHEMA_TITLES = {
    "schemas/b2c_module_manifest.schema.json": "WJX B2C Module Manifest",
    "schemas/b2c_action_contract.schema.json": "WJX B2C Action Contract",
    "schemas/explanation_trace.schema.json": "WJX Explanation Trace",
    "schemas/field_proposal.schema.json": "WJX Field Proposal",
    "schemas/skill_definition.schema.json": "WJX Skill Definition",
    "schemas/research_artifact.schema.json": "WJX Research Artifact",
}


# 本段代码核心功能：从脚本所在位置向上定位仓库根目录。
# - 输入：脚本的绝对路径及必须存在的PROJECT_MEMORY.md标志文件。
# - 处理：依次检查当前目录及其父目录，找到第一个包含权威文件的目录。
# - 输出：返回仓库根目录Path；找不到时抛出RuntimeError。
# - 常量依据：PROJECT_MEMORY.md是本项目长期权威文件，适合作为稳定仓库标志。
# - 为什么这样写：验证脚本可从仓库根目录、scripts目录或修改包验证入口运行，减少用户路径错误。
def locate_repository_root() -> Path:
    script_path = Path(__file__).resolve()
    for candidate in (script_path.parent, *script_path.parents):
        if (candidate / "PROJECT_MEMORY.md").is_file():
            return candidate
    raise RuntimeError("无法定位包含PROJECT_MEMORY.md的仓库根目录。")


# 本段代码核心功能：验证本任务要求的文件是否全部存在且不是空文件。
# - 输入：仓库根目录和REQUIRED_FILES清单。
# - 处理：逐个拼接相对路径并检查文件类型与字节大小。
# - 输出：返回错误消息列表；空列表代表文件存在性通过。
# - 为什么这样写：修改包漏打文件是多文件任务最常见的低级交付错误，应在用户应用前阻断。
def validate_required_files(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"缺少文件：{relative_path}")
        elif path.stat().st_size == 0:
            errors.append(f"空文件：{relative_path}")
    return errors


# 本段代码核心功能：验证权威文件是否真正写入双视图、Skill、白箱和当前任务保持原则。
# - 输入：仓库根目录和按文件分组的关键短语。
# - 处理：按UTF-8读取Markdown并检查每个短语是否存在。
# - 输出：返回缺失短语错误列表。
# - 为什么这样写：只检查文件存在会允许空壳或旧版本通过，关键短语验证能证明设计内容已经落地。
def validate_authority_content(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path, phrases in REQUIRED_PHRASES.items():
        text = (root / relative_path).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{relative_path} 缺少关键内容：{phrase}")
    return errors


# 本段代码核心功能：验证六个JSON Schema能够解析并包含统一的2020-12版本、标题和对象约束。
# - 输入：仓库根目录和SCHEMA_TITLES清单。
# - 处理：使用Python标准库解析JSON，核对$schema、title、type、required和properties。
# - 输出：返回格式或结构错误列表。
# - 常量依据：项目接入中心已采用JSON Schema 2020-12，新B2C合同继续复用同一标准而不另造语言。
# - 为什么这样写：标准库验证不引入新依赖，能在用户现有虚拟环境和沙盒中稳定运行。
def validate_schemas(root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path, expected_title in SCHEMA_TITLES.items():
        path = root / relative_path
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{relative_path} 无法解析：{exc}")
            continue
        if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{relative_path} 未使用JSON Schema 2020-12。")
        if payload.get("title") != expected_title:
            errors.append(f"{relative_path} title不匹配。")
        if payload.get("type") != "object":
            errors.append(f"{relative_path} 根类型必须为object。")
        if not isinstance(payload.get("required"), list) or not payload["required"]:
            errors.append(f"{relative_path} 缺少required合同。")
        if not isinstance(payload.get("properties"), dict) or not payload["properties"]:
            errors.append(f"{relative_path} 缺少properties合同。")
    return errors


# 本段代码核心功能：检查新权威文件不再绑定已停用的具体执行工具，也不重新引入已淘汰的开发型Skill。
# - 输入：六份核心入口和架构文件。
# - 处理：搜索明确禁止作为长期依赖的名称；历史任务报告不在本任务扫描范围内。
# - 输出：返回发现的过期引用。
# - 为什么这样写：长期权威文件应描述稳定能力和工作纪律，不能让旧工具或已拒绝Skill重新进入默认路线。
def validate_obsolete_references(root: Path) -> list[str]:
    errors: list[str] = []
    scoped_files = (
        "PROJECT_MEMORY.md",
        "SYSTEM_ARCHITECTURE.md",
        "DEVELOPMENT_GUIDANCE.md",
        "PROJECT_CONTEXT.md",
        "README_PROJECT_MEMORY.md",
        "START_HERE.md",
        "B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md",
        "SKILL_PLATFORM_ARCHITECTURE.md",
    )
    forbidden_terms = ("Codex", "brainstorming")
    for relative_path in scoped_files:
        text = (root / relative_path).read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in text:
                errors.append(f"{relative_path} 仍包含过期默认依赖：{term}")
    return errors


# 本段代码核心功能：汇总全部验收结果并提供适合PowerShell和CI读取的退出码。
# - 输入：各验证函数返回的错误列表。
# - 处理：合并错误，逐条输出；无错误时输出任务通过摘要。
# - 输出：成功返回0，失败返回1。
# - 为什么这样写：明确退出码可以阻断apply脚本后续Git提交，避免权威文件未完成时被推送。
def main() -> int:
    root = locate_repository_root()
    errors = [
        *validate_required_files(root),
        *validate_authority_content(root),
        *validate_schemas(root),
        *validate_obsolete_references(root),
    ]
    if errors:
        print("TASK_025A_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASK_025A_VALIDATION_PASSED")
    print(f"repository_root={root}")
    print(f"validated_files={len(REQUIRED_FILES)}")
    print(f"validated_schemas={len(SCHEMA_TITLES)}")
    return 0


# 本段代码核心功能：仅在脚本作为命令行入口执行时运行主验证流程。
# - 输入：Python解释器提供的__name__运行标志。
# - 处理：调用main并把返回值交给SystemExit。
# - 输出：向PowerShell、CI或用户终端提供可靠退出码。
# - 为什么这样写：模块被单元测试导入时不会自动执行文件系统验证，便于复用内部函数。
if __name__ == "__main__":
    sys.exit(main())
