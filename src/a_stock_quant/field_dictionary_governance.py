# 模块总览：当前模块。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# 变量更新：计算并保存EXPECTED_DICTIONARY_REVISION，右侧逻辑为`'0.6.0'`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
EXPECTED_DICTIONARY_REVISION = "0.6.0"
# 变量更新：计算并保存EXPECTED_VALUE_DOMAIN_KINDS，右侧逻辑为`{'CLOSED_ENUM', 'CONTROLLED_CODESET', 'OPEN_CODE', 'IDENTIFIER', 'FREE_TEXT'}`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
EXPECTED_VALUE_DOMAIN_KINDS = {
    "CLOSED_ENUM",
    "CONTROLLED_CODESET",
    "OPEN_CODE",
    "IDENTIFIER",
    "FREE_TEXT",
}


# 定义GovernanceIssue强类型合同，集中保存相关状态、参数和校验规则。
# - 字段severity：类型str。
# - 字段code：类型str。
# - 字段message：类型str。
# - 字段evidence：类型dict[str, Any] | None，默认值None。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True)
class GovernanceIssue:
    # 变量更新：计算并保存severity，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    severity: str
    # 变量更新：计算并保存code，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    code: str
    # 变量更新：计算并保存message，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    message: str
    # 变量更新：计算并保存evidence，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    evidence: dict[str, Any] | None = None


# 执行load_yaml逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def load_yaml(path: Path) -> dict[str, Any]:
    # 变量更新：计算并保存payload，右侧逻辑为`yaml.safe_load(path.read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(payload, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(payload, dict):
        # 错误阻断：抛出`ValueError(f'YAML根节点必须是字典：{path}')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise ValueError(f"YAML根节点必须是字典：{path}")
    # 结果返回：把`payload`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return payload


# 执行field_index逻辑，把输入参数转换为受合同约束的结果。
# - 参数canonical：类型dict[str, Any]；进入函数后按合同校验或参与计算。
# - 输出：返回类型dict[tuple[str, str], dict[str, Any]]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def field_index(
    canonical: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    # 变量更新：计算并保存result，右侧逻辑为`{}`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    result: dict[tuple[str, str], dict[str, Any]] = {}
    # 迭代处理：依次读取`canonical.get('domains', [])`中的元素，并绑定到`domain`。
    # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
    # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
    for domain in canonical.get("domains", []):
        # 变量更新：计算并保存domain_code，右侧逻辑为`str(domain.get('domain_code', ''))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        domain_code = str(domain.get("domain_code", ""))
        # 迭代处理：依次读取`domain.get('fields', [])`中的元素，并绑定到`field`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field in domain.get("fields", []):
            # 变量更新：计算并保存key，右侧逻辑为`(domain_code, str(field.get('canonical_name', '')))`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            key = (domain_code, str(field.get("canonical_name", "")))
            # 条件门禁：判断`key in result`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if key in result:
                # 错误阻断：抛出`ValueError(f'字段重复：{key}')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise ValueError(f"字段重复：{key}")
            # 变量更新：计算并保存result[key]，右侧逻辑为`field`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            result[key] = field
    # 结果返回：把`result`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return result


# 执行occurrences_by_name逻辑，把输入参数转换为受合同约束的结果。
# - 参数canonical：类型dict[str, Any]；进入函数后按合同校验或参与计算。
# - 输出：返回类型dict[str, list[tuple[str, dict[str, Any]]]]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def occurrences_by_name(
    canonical: dict[str, Any],
) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    # 变量更新：计算并保存result，右侧逻辑为`defaultdict(list)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    result: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    # 迭代处理：依次读取`canonical.get('domains', [])`中的元素，并绑定到`domain`。
    # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
    # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
    for domain in canonical.get("domains", []):
        # 变量更新：计算并保存domain_code，右侧逻辑为`str(domain.get('domain_code', ''))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        domain_code = str(domain.get("domain_code", ""))
        # 迭代处理：依次读取`domain.get('fields', [])`中的元素，并绑定到`field`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field in domain.get("fields", []):
            # API调用：执行`result[str(field.get('canonical_name', ''))].append((domain_code, field))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            result[str(field.get("canonical_name", ""))].append(
                (domain_code, field)
            )
    # 结果返回：把`result`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return result


# 执行signature逻辑，把输入参数转换为受合同约束的结果。
# - 参数field：类型dict[str, Any]；进入函数后按合同校验或参与计算。
# - 输出：返回类型tuple[str, str, str]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def signature(field: dict[str, Any]) -> tuple[str, str, str]:
    # 结果返回：把`(str(field.get('data_type', '')).upper(), str(field.get('unit', '')).lower(), str(field.get('time...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return (
        str(field.get("data_type", "")).upper(),
        str(field.get("unit", "")).lower(),
        str(field.get("time_semantics", "")),
    )


# 执行validate_dictionary_governance逻辑，把输入参数转换为受合同约束的结果。
# - 参数project_root：类型Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def validate_dictionary_governance(
    project_root: Path,
) -> dict[str, Any]:
    # 变量更新：计算并保存schema_dir，右侧逻辑为`project_root / 'schemas'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    schema_dir = project_root / "schemas"
    # 变量更新：计算并保存canonical，右侧逻辑为`load_yaml(schema_dir / 'canonical_fields.yaml')`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical = load_yaml(schema_dir / "canonical_fields.yaml")
    # 变量更新：计算并保存contract，右侧逻辑为`load_yaml(schema_dir / 'field_governance_contract.yaml')`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    contract = load_yaml(schema_dir / "field_governance_contract.yaml")
    # 变量更新：计算并保存enums，右侧逻辑为`load_yaml(schema_dir / 'enum_definitions.yaml')`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    enums = load_yaml(schema_dir / "enum_definitions.yaml")

    # 变量更新：计算并保存issues，右侧逻辑为`[]`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    issues: list[GovernanceIssue] = []
    # 变量更新：计算并保存index，右侧逻辑为`field_index(canonical)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    index = field_index(canonical)

    # 变量更新：计算并保存canonical_revision，右侧逻辑为`str(canonical.get('dictionary_revision', ''))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_revision = str(canonical.get("dictionary_revision", ""))
    # 变量更新：计算并保存contract_revision，右侧逻辑为`str(contract.get('dictionary_revision', ''))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    contract_revision = str(contract.get("dictionary_revision", ""))
    # 条件门禁：判断`canonical_revision != EXPECTED_DICTIONARY_REVISION`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if canonical_revision != EXPECTED_DICTIONARY_REVISION:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'DICTIONARY_REVISION_MISMATCH', 'canonical_fields.yaml修订号不...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "DICTIONARY_REVISION_MISMATCH",
                "canonical_fields.yaml修订号不符合当前治理合同。",
                {"actual": canonical_revision},
            )
        )
    # 条件门禁：判断`contract_revision != canonical_revision`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if contract_revision != canonical_revision:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'CONTRACT_REVISION_MISMATCH', '治理合同与字段字典修订号不一致。', {'canoni...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "CONTRACT_REVISION_MISMATCH",
                "治理合同与字段字典修订号不一致。",
                {
                    "canonical": canonical_revision,
                    "contract": contract_revision,
                },
            )
        )

    # 变量更新：计算并保存actual_kinds，右侧逻辑为`set(contract.get('value_domain_kinds', {}))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    actual_kinds = set(contract.get("value_domain_kinds", {}))
    # 条件门禁：判断`actual_kinds != EXPECTED_VALUE_DOMAIN_KINDS`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if actual_kinds != EXPECTED_VALUE_DOMAIN_KINDS:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'VALUE_DOMAIN_KINDS_INVALID', 'value_domain_kinds不完整。', {'...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "VALUE_DOMAIN_KINDS_INVALID",
                "value_domain_kinds不完整。",
                {
                    "expected": sorted(EXPECTED_VALUE_DOMAIN_KINDS),
                    "actual": sorted(actual_kinds),
                },
            )
        )

    # 迭代处理：依次读取`contract.get('required_metadata', [])`中的元素，并绑定到`requirement`。
    # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
    # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
    for requirement in contract.get("required_metadata", []):
        # 变量更新：计算并保存key，右侧逻辑为`(str(requirement.get('domain_code', '')), str(requirement.get('canonical_name', '')))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        key = (
            str(requirement.get("domain_code", "")),
            str(requirement.get("canonical_name", "")),
        )
        # 变量更新：计算并保存field，右侧逻辑为`index.get(key)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        field = index.get(key)
        # 条件门禁：判断`field is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if field is None:
            # API调用：执行`issues.append(GovernanceIssue('ERROR', 'REQUIRED_FIELD_MISSING', '治理合同引用的字段不存在。', {'field': key}))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            issues.append(
                GovernanceIssue(
                    "ERROR",
                    "REQUIRED_FIELD_MISSING",
                    "治理合同引用的字段不存在。",
                    {"field": key},
                )
            )
            continue
        # 变量更新：计算并保存metadata_key，右侧逻辑为`str(requirement.get('key', ''))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        metadata_key = str(requirement.get("key", ""))
        # 变量更新：计算并保存expected_value，右侧逻辑为`requirement.get('value')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        expected_value = requirement.get("value")
        # 变量更新：计算并保存actual_value，右侧逻辑为`field.get(metadata_key)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        actual_value = field.get(metadata_key)
        # 条件门禁：判断`actual_value != expected_value`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if actual_value != expected_value:
            # API调用：执行`issues.append(GovernanceIssue('ERROR', 'REQUIRED_METADATA_MISMATCH', '字段治理元数据不符合合同。', {'field': k...`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            issues.append(
                GovernanceIssue(
                    "ERROR",
                    "REQUIRED_METADATA_MISMATCH",
                    "字段治理元数据不符合合同。",
                    {
                        "field": key,
                        "key": metadata_key,
                        "expected": expected_value,
                        "actual": actual_value,
                    },
                )
            )

    # 变量更新：计算并保存contracts，右侧逻辑为`{str(item.get('canonical_name', '')): item for item in contract.get('shared_field_contr...`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    contracts = {
        str(item.get("canonical_name", "")): item
        for item in contract.get("shared_field_contracts", [])
    }
    # 变量更新：计算并保存accepted_drift_names，右侧逻辑为`set(contracts)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    accepted_drift_names = set(contracts)

    # 变量更新：计算并保存ungoverned_drift，右侧逻辑为`{}`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ungoverned_drift: dict[str, list[dict[str, Any]]] = {}
    # 迭代处理：依次读取`occurrences_by_name(canonical).items()`中的元素，并绑定到`(name, occurrences)`。
    # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
    # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
    for name, occurrences in occurrences_by_name(canonical).items():
        # 变量更新：计算并保存signatures，右侧逻辑为`{signature(field) for _, field in occurrences}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        signatures = {signature(field) for _, field in occurrences}
        # 条件门禁：判断`len(signatures) <= 1`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(signatures) <= 1:
            continue
        # 条件门禁：判断`name not in accepted_drift_names`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if name not in accepted_drift_names:
            # 变量更新：计算并保存ungoverned_drift[name]，右侧逻辑为`[{'domain_code': domain_code, 'signature': signature(field)} for domain_code, field in ...`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            ungoverned_drift[name] = [
                {
                    "domain_code": domain_code,
                    "signature": signature(field),
                }
                for domain_code, field in occurrences
            ]

    # 条件门禁：判断`ungoverned_drift`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if ungoverned_drift:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'UNGOVERNED_CROSS_DOMAIN_DRIFT', '仍有未登记的跨Domain同名字段签名漂移。',...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "UNGOVERNED_CROSS_DOMAIN_DRIFT",
                "仍有未登记的跨Domain同名字段签名漂移。",
                ungoverned_drift,
            )
        )

    # 变量更新：计算并保存trade_contract，右侧逻辑为`contracts.get('trade_count', {})`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    trade_contract = contracts.get("trade_count", {})
    # 条件门禁：判断`trade_contract.get('resolution') != 'SEMANTIC_COLLISION_MIGRATION_REQUIRED'`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if (
        trade_contract.get("resolution")
        != "SEMANTIC_COLLISION_MIGRATION_REQUIRED"
    ):
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'TRADE_COUNT_MIGRATION_MISSING', 'trade_count语义冲突未进入迁移计划。'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "TRADE_COUNT_MIGRATION_MISSING",
                "trade_count语义冲突未进入迁移计划。",
            )
        )
    # 变量更新：计算并保存migration，右侧逻辑为`trade_contract.get('migration', {})`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    migration = trade_contract.get("migration", {})
    # 条件门禁：判断`migration.get('breaking_change_allowed') is not False`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if migration.get("breaking_change_allowed") is not False:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'BREAKING_CHANGE_GUARD_MISSING', 'trade_count迁移必须禁止直接破坏性修改...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "BREAKING_CHANGE_GUARD_MISSING",
                "trade_count迁移必须禁止直接破坏性修改。",
            )
        )
    # 条件门禁：判断`('backtest', 'executed_trade_count') in index`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if ("backtest", "executed_trade_count") in index:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'PREMATURE_TRADE_COUNT_RENAME', 'TASK_015C-1仅登记迁移计划，不应直接新增...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "PREMATURE_TRADE_COUNT_RENAME",
                "TASK_015C-1仅登记迁移计划，不应直接新增或替换字段。",
            )
        )

    # 变量更新：计算并保存value_contract，右侧逻辑为`contracts.get('value_numeric', {})`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    value_contract = contracts.get("value_numeric", {})
    # 条件门禁：判断`value_contract.get('resolution') != 'CONTEXTUAL_TYPE_VARIANT_ALLOWED'`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if (
        value_contract.get("resolution")
        != "CONTEXTUAL_TYPE_VARIANT_ALLOWED"
    ):
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'VALUE_NUMERIC_EXCEPTION_MISSING', 'value_numeric上下文类型差异未登...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "VALUE_NUMERIC_EXCEPTION_MISSING",
                "value_numeric上下文类型差异未登记。",
            )
        )


    # 变量更新：计算并保存expected_precision_values，右侧逻辑为`{'EXACT_TIMESTAMP', 'SECOND', 'MINUTE', 'DATE_ONLY', 'UNKNOWN'}`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    expected_precision_values = {
        "EXACT_TIMESTAMP",
        "SECOND",
        "MINUTE",
        "DATE_ONLY",
        "UNKNOWN",
    }
    # 变量更新：计算并保存actual_precision_values，右侧逻辑为`set(enums.get('snapshot_time_precision', []))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    actual_precision_values = set(
        enums.get("snapshot_time_precision", [])
    )
    # 条件门禁：判断`actual_precision_values != expected_precision_values`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if actual_precision_values != expected_precision_values:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'SNAPSHOT_TIME_PRECISION_ENUM_INVALID', 'snapshot_time_pre...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "SNAPSHOT_TIME_PRECISION_ENUM_INVALID",
                "snapshot_time_precision枚举不完整。",
                {
                    "expected": sorted(expected_precision_values),
                    "actual": sorted(actual_precision_values),
                },
            )
        )

    # 变量更新：计算并保存auction_time，右侧逻辑为`index.get(('auction', 'snapshot_time'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    auction_time = index.get(("auction", "snapshot_time"))
    # 变量更新：计算并保存auction_precision，右侧逻辑为`index.get(('auction', 'snapshot_time_precision'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    auction_precision = index.get(
        ("auction", "snapshot_time_precision")
    )
    # 条件门禁：判断`auction_time is None or auction_time.get('nullable') is not True`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if auction_time is None or auction_time.get("nullable") is not True:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'AUCTION_TIME_NULLABILITY_INVALID', '日期级竞价来源要求snapshot_tim...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "AUCTION_TIME_NULLABILITY_INVALID",
                "日期级竞价来源要求snapshot_time可空。",
            )
        )
    # 条件门禁：判断`auction_time is not None and auction_time.get('time_semantics') != 'observation_time'`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if (
        auction_time is not None
        and auction_time.get("time_semantics")
        != "observation_time"
    ):
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'AUCTION_TIME_SEMANTICS_INVALID', 'snapshot_time必须声明observ...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "AUCTION_TIME_SEMANTICS_INVALID",
                "snapshot_time必须声明observation_time。",
            )
        )
    # 条件门禁：判断`auction_precision is None or auction_precision.get('nullable') is not False or auction_precision....`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if (
        auction_precision is None
        or auction_precision.get("nullable") is not False
        or auction_precision.get("enum_ref")
        != "snapshot_time_precision"
    ):
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'AUCTION_TIME_PRECISION_FIELD_INVALID', 'snapshot_time_pre...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "AUCTION_TIME_PRECISION_FIELD_INVALID",
                "snapshot_time_precision必须非空并绑定枚举。",
            )
        )

    # 变量更新：计算并保存object_domains，右侧逻辑为`{str(domain.get('canonical_object', '')): domain for domain in canonical.get('domains',...`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    object_domains = {
        str(domain.get("canonical_object", "")): domain
        for domain in canonical.get("domains", [])
    }
    # 变量更新：计算并保存classification_market，右侧逻辑为`object_domains.get('ClassificationMarketSnapshot')`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    classification_market = object_domains.get(
        "ClassificationMarketSnapshot"
    )
    # 变量更新：计算并保存required_classification_fields，右侧逻辑为`{'classification_system', 'classification_type', 'node_id', 'node_name_cn', 'trade_date...`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_classification_fields = {
        "classification_system",
        "classification_type",
        "node_id",
        "node_name_cn",
        "trade_date",
        "snapshot_phase",
        "pct_change_pct",
        "up_count",
        "down_count",
        "breadth_ratio",
        "breadth_status",
        "volume_lots",
        "volume_shares",
        "amount_cny",
    }
    # 条件门禁：判断`classification_market is None`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if classification_market is None:
        # API调用：执行`issues.append(GovernanceIssue('ERROR', 'CLASSIFICATION_MARKET_OBJECT_MISSING', '缺少ClassificationM...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        issues.append(
            GovernanceIssue(
                "ERROR",
                "CLASSIFICATION_MARKET_OBJECT_MISSING",
                "缺少ClassificationMarketSnapshot对象。",
            )
        )
    # 备用分支：当前面的条件不满足时执行此路径。
    # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
    else:
        # 变量更新：计算并保存actual_fields，右侧逻辑为`{str(field.get('canonical_name', '')) for field in classification_market.get('fields', ...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        actual_fields = {
            str(field.get("canonical_name", ""))
            for field in classification_market.get("fields", [])
        }
        # 变量更新：计算并保存missing_fields，右侧逻辑为`sorted(required_classification_fields - actual_fields)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        missing_fields = sorted(
            required_classification_fields - actual_fields
        )
        # 条件门禁：判断`missing_fields`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if missing_fields:
            # API调用：执行`issues.append(GovernanceIssue('ERROR', 'CLASSIFICATION_MARKET_FIELDS_MISSING', 'ClassificationMar...`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            issues.append(
                GovernanceIssue(
                    "ERROR",
                    "CLASSIFICATION_MARKET_FIELDS_MISSING",
                    "ClassificationMarketSnapshot缺少核心字段。",
                    {"missing": missing_fields},
                )
            )

    # 变量更新：计算并保存issue_rows，右侧逻辑为`[{'severity': item.severity, 'code': item.code, 'message': item.message, 'evidence': it...`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    issue_rows = [
        {
            "severity": item.severity,
            "code": item.code,
            "message": item.message,
            "evidence": item.evidence,
        }
        for item in issues
    ]
    # 变量更新：计算并保存errors，右侧逻辑为`[item for item in issue_rows if item['severity'] == 'ERROR']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    errors = [item for item in issue_rows if item["severity"] == "ERROR"]

    # 结果返回：把`{'task_id': 'FIELD_DICTIONARY_GOVERNANCE', 'overall_status': 'PASSED' if not errors else 'FAILED'...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return {
        "task_id": "FIELD_DICTIONARY_GOVERNANCE",
        "overall_status": "PASSED" if not errors else "FAILED",
        "dictionary_revision": canonical_revision,
        "contract_revision": contract.get("contract_revision"),
        "required_metadata_count": len(
            contract.get("required_metadata", [])
        ),
        "shared_field_contract_count": len(
            contract.get("shared_field_contracts", [])
        ),
        "value_domain_kind_count": len(actual_kinds),
        "issues": issue_rows,
    }
