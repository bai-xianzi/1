# 本脚本核心功能：在不连接数据库的情况下校验 TASK_022 的真实配置、强类型合同和插件入口。
# - 输入：已经应用 TASK_022 的项目工作区。
# - 输出：合同全部满足时返回 0，否则抛出明确断言并阻断后续真实验收。
# - 为什么这样写：先用低成本离线门禁发现配置错误，可以避免无意义地连接真实数据库。
"""TASK_022 离线配置和导入边界校验。"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
from pathlib import Path


# 断言辅助：把布尔合同转换为带业务语义的失败信息。
# - 参数 condition：必须为真的合同结果；message：失败时显示的原因。
# - 输出：合同成立时无返回值，失败时抛出 AssertionError。
# - 为什么这样写：统一断言格式让 PowerShell 和人工排查都能快速定位配置缺口。
def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# 源码字面量检查：只检查 Python 可执行语法树中的字符串常量，不扫描注释文本。
# - 输入 source：UTF-8 Python 源码；target：不得继续作为运行时常量存在的警告代码。
# - 输出：语法树中存在完全相同字符串字面量时返回 True，否则返回 False。
# - 为什么这样写：教学式注释可能保留历史警告名称；原始全文搜索会把注释误判为运行时代码。
def contains_string_literal(source: str, target: str) -> bool:
    tree = ast.parse(source)
    return any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value == target
        for node in ast.walk(tree)
    )


# 主校验流程：读取注册表和能力矩阵，并同时使用项目强类型加载器验证值域和交叉约束。
# - 输入：--project-root 指向本地健康仓库。
# - 输出：全部合同满足返回 0。
# - 为什么这样写：原始 JSON 检查与强类型对象检查结合，既验证字段值，也验证项目正式解析路径。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    registry_path = root / "configs/providers/provider_plugin_registry_v0.json"
    matrix_path = root / "configs/providers/provider_capability_matrix_v0.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))

    # TASK_020A 和 TASK_020B 是强类型合同身份，不是最近修改任务号。
    require(matrix.get("task_id") == "TASK_020A", "能力矩阵 task_id 必须保持 TASK_020A")
    require(registry.get("task_id") == "TASK_020B", "插件注册表 task_id 必须保持 TASK_020B")

    entries = [item for item in registry["entries"] if item["provider_id"] == "local_dolphindb"]
    require(len(entries) == 1, "local_dolphindb 注册项数量必须为 1")
    entry = entries[0]
    require(entry["plugin_id"] == "builtin.local_dolphindb.plugin_bridge", "plugin_id 未升级")
    require(entry["registration_status"] == "AVAILABLE", "注册状态不是 AVAILABLE")
    require(entry["enabled_for_routing"] is True, "local_dolphindb 未启用路由")
    require(bool(entry["discovery_result_ref"]), "缺少发现结果引用")
    require(entry["authentication_reference_ref"] == "env://DOLPHINDB_PASSWORD", "认证引用异常")
    enabled = [item["provider_id"] for item in registry["entries"] if item["enabled_for_routing"]]
    require(enabled == ["local_dolphindb"], f"启用的 Provider 异常：{enabled}")
    require(registry["automatic_activation_allowed"] is False, "不得开启全局自动激活")

    targets = [item for item in matrix["provider_targets"] if item["provider_id"] == "local_dolphindb"]
    require(len(targets) == 1, "local_dolphindb 能力项数量必须为 1")
    target = targets[0]
    require(target["lifecycle"] == "ACTIVATED", "生命周期不是 ACTIVATED")
    require(target["discovery_status"] == "DISCOVERY_COMPLETE", "发现状态不是 DISCOVERY_COMPLETE")
    require(target["execution_capability"] is False, "不得启用交易执行能力")
    for capability in (
        "EOD_MARKET_DATA",
        "FUNDAMENTAL_DATA",
        "CLASSIFICATION_DATA",
        "MONEY_FLOW",
        "AUCTION_DATA",
    ):
        require(target["capabilities"].get(capability) == "VERIFIED", f"{capability} 未标记 VERIFIED")

    # 使用项目正式强类型加载器验证配置值域和交叉约束。
    from a_stock_quant.provider_capabilities import load_provider_capability_matrix
    from a_stock_quant.provider_plugin_protocol import load_provider_plugin_registry

    loaded_matrix = load_provider_capability_matrix(matrix_path)
    loaded_registry = load_provider_plugin_registry(registry_path)
    require(loaded_matrix.provider("local_dolphindb").lifecycle.value == "ACTIVATED", "强类型矩阵未加载激活状态")
    loaded_entry = next(item for item in loaded_registry.entries if item.provider_id == "local_dolphindb")
    require(loaded_entry.enabled_for_routing, "强类型注册表未启用路由")

    module_name, class_name = entry["entrypoint"].split(":", 1)
    module = importlib.import_module(module_name)
    require(hasattr(module, class_name), f"入口类不存在：{entry['entrypoint']}")

    # 只检查运行时字符串字面量；教学式注释中的历史文字不属于可执行警告。
    source = (root / "src/a_stock_quant/dolphindb_provider_plugin.py").read_text(encoding="utf-8-sig")
    require(
        not contains_string_literal(source, "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK"),
        "运行时代码仍包含已完成的注册表激活警告",
    )

    print("TASK_022 离线激活合同校验通过。")
    return 0


# 脚本入口：把离线合同校验的退出码交给上层 PowerShell 门禁。
# - 输入：操作系统命令行参数。
# - 为什么这样写：失败必须成为非零退出码，防止继续连接真实数据库或提交代码。
if __name__ == "__main__":
    raise SystemExit(main())
