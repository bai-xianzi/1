# 本脚本核心功能：使用跨Python版本稳定的Token语义摘要验证TASK_021C只增加教学式注释。
# - argparse接收项目根目录。
# - tokenize保留缩进、常量、调用参数和控制流，排除注释与非语义空行。
# - importlib加载统一教学式注释审计器。
# - 为什么这样写：用户机器与补丁生成机器Python版本不同，不能持久化ast.dump默认文本哈希。
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import io
import json
import sys
import tokenize
from pathlib import Path


# 便携语义摘要：将Python源码转换为忽略注释和非语义空行的Token序列，再计算SHA256。
# - tokenize完成词法分析，Token类型和源码值不依赖ast.dump的版本显示格式。
# - COMMENT、NL、ENCODING和ENDMARKER不影响可执行逻辑，因此排除。
# - NEWLINE统一为\n，避免Windows与Linux换行符差异。
# - INDENT、DEDENT、名称、数值、字符串、运算符等全部保留，所以逻辑变化仍会改变摘要。
# - 为什么这样写：ast.dump默认文本会随Python版本变化，Token序列更适合跨机器持久验证。
def semantic_token_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    parts: list[str] = []
    ignored = {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in ignored:
            continue
        value = "\n" if token.type == tokenize.NEWLINE else token.string
        parts.append(f"{token.type}:{value}")
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


# 审计器加载：动态导入项目统一注释审计脚本。
# - sys.modules注册保证dataclass等装饰器可以回查模块。
# - 为什么这样写：验证器和Git门禁必须复用同一审计实现。
def load_audit_module(path: Path):
    spec = importlib.util.spec_from_file_location("task_021c_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载教学式注释审计器。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

# 合同断言：条件不成立时立即抛出明确错误。
# - 为什么这样写：PowerShell必须收到非零退出码，不能把失败当警告。
def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

# 主验证流程：逐文件核对便携语义摘要、注释数量、审计结果与Git阻断状态。
# - 为什么这样写：同时证明业务Token不变、注释结构合格，并消除Python版本误报。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report = json.loads((root / "reports/task_021c_readiness_market_state_comment_migration.json").read_text(encoding="utf-8"))
    audit_module = load_audit_module(root / "scripts" / "audit_teaching_comments.py")
    require(report["task_id"] == "TASK_021C", "task_id异常。")
    require(report["target_file_count"] == 9, "目标文件数量异常。")
    require(report["semantic_verification_method"] == "PYTHON_TOKEN_STREAM_V1", "语义验证方法异常。")
    require(report["semantic_token_identity_required"] is True, "便携语义一致性必须启用。")
    require(report["business_logic_changed"] is False, "报告错误声明业务逻辑变化。")
    require(report["github_commit_allowed"] is False, "迁移中不得允许Git提交。")
    require(report["github_push_allowed"] is False, "迁移中不得允许GitHub推送。")

    require(report["database_write_operation_count"] == 0, "本批不得包含数据库写操作。")

    violations: dict[str, list[str]] = {}
    for item in report["files"]:
        relative_path = item["path"]
        path = root / relative_path
        require(path.exists(), f"缺少迁移文件：{relative_path}")
        require(semantic_token_sha256(path) == item["semantic_token_sha256"], f"Token语义发生变化：{relative_path}")
        current_comments = sum(line.lstrip().startswith("#") for line in path.read_text(encoding="utf-8").splitlines())
        require(current_comments == item["after_comment_line_count"], f"注释行数量异常：{relative_path}")
        result = audit_module.audit_python_file(root, path)
        if result.violations:
            violations[relative_path] = list(result.violations)

    require(not violations, "TASK_021C仍有注释违规：" + json.dumps(violations, ensure_ascii=False))
    output = {
        "task_id": "TASK_021C",
        "overall_status": "PASSED",
        "target_file_count": report["target_file_count"],
        "added_comment_line_count": report["added_comment_line_count"],
        "semantic_verification_method": report["semantic_verification_method"],
        "semantic_token_identity": True,
        "batch_comment_violation_count": 0,
        "business_logic_changed": False,

        "database_write_operation_count": 0,
        "github_commit_allowed": False,
        "github_push_allowed": False,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0

# 脚本入口：把主流程退出码交给操作系统。
# - 为什么这样写：任何异常都必须停止后续迁移。
if __name__ == "__main__":
    raise SystemExit(main())
