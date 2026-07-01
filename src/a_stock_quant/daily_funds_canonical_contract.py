# 模块总览：校验七类日线行情、竞价与资金流数据映射到Canonical对象时必须遵守的合同。
# - 输入输出：输入为YAML合同和字段字典；输出为可审计的合同版本、数据集状态和问题清单。
# - 数据与安全：本模块只读取本地配置，不连接DolphinDB，也不写入任何业务数据。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""七类日线资金Canonical接入合同验证。"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`from dataclasses import dataclass`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from dataclasses import dataclass
# 依赖导入：加载`from pathlib import Path`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：加载`from typing import Any`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any

# 依赖导入：加载`import yaml`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import yaml


# 关键常量REQUIRED_DATASETS：集中保存`('hq', 'hy', 'gn', 'kphq', 'kphy', 'kpgn', 'zj')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
REQUIRED_DATASETS = (
    "hq",
    "hy",
    "gn",
    "kphq",
    "kphy",
    "kpgn",
    "zj",
)
# 关键常量CLASSIFICATION_DATASETS：集中保存`frozenset({'hy', 'gn', 'kphy', 'kpgn'})`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
CLASSIFICATION_DATASETS = frozenset(
    {"hy", "gn", "kphy", "kpgn"}
)
# 关键常量ALLOWED_STATUSES：集中保存`frozenset({'MAPPED', 'MAPPED_WITH_WARNING', 'DERIVED', 'CONSTANT', 'SOURCE_EXTENSION', 'BLOCKED_SCH…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
ALLOWED_STATUSES = frozenset(
    {
        "MAPPED",
        "MAPPED_WITH_WARNING",
        "DERIVED",
        "CONSTANT",
        "SOURCE_EXTENSION",
        "BLOCKED_SCHEMA_GAP",
        "NOT_APPLICABLE",
    }
)


# 类DailyFundsCanonicalContractError：Canonical合同无效。
# - 结构：继承或实现ValueError；类体约包含0个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DailyFundsCanonicalContractError(ValueError):
    """Canonical合同无效。"""


# 类DailyFundsCanonicalContract：集中管理DailyFundsCanonicalContract相关状态和不变量。
# - 结构：继承或实现object；类体约包含1个字段或常量、3个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DailyFundsCanonicalContract:
    # 状态计算：把`无`的结果保存到`raw`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    raw: dict[str, Any]

    # 函数contract_version：执行contract_version对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def contract_version(self) -> str:
        # 结果返回：把`str(self.raw['contract_version'])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(self.raw["contract_version"])

    # 函数dictionary_revision：执行dictionary_revision对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def dictionary_revision(self) -> str:
        # 结果返回：把`str(self.raw['dictionary_revision'])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(self.raw["dictionary_revision"])

    # 函数datasets：执行datasets对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def datasets(self) -> dict[str, dict[str, Any]]:
        # 结果返回：把`dict(self.raw['datasets'])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return dict(self.raw["datasets"])


# 函数_load_yaml：执行_load_yaml对应的业务处理。
# - 输入：path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _load_yaml(path: Path) -> dict[str, Any]:
    # 状态计算：把`yaml.safe_load(path.read_text(encoding='utf-8'))`的结果保存到`payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(payload, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(payload, dict):
        # 错误阻断：抛出`DailyFundsCanonicalContractError(f'YAML根节点必须是映射：{path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsCanonicalContractError(
            f"YAML根节点必须是映射：{path}"
        )
    # 结果返回：把`payload`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return payload


# 函数load_contract：执行load_contract对应的业务处理。
# - 输入：path:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型DailyFundsCanonicalContract；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def load_contract(path: str | Path) -> DailyFundsCanonicalContract:
    # 结果返回：把`DailyFundsCanonicalContract(raw=_load_yaml(Path(path)))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return DailyFundsCanonicalContract(raw=_load_yaml(Path(path)))


# 函数_dictionary_objects：执行_dictionary_objects对应的业务处理。
# - 输入：dictionary_path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, set[str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _dictionary_objects(
    dictionary_path: Path,
) -> dict[str, set[str]]:
    # 状态计算：把`_load_yaml(dictionary_path)`的结果保存到`payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    payload = _load_yaml(dictionary_path)
    # 状态计算：把`{}`的结果保存到`objects`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    objects: dict[str, set[str]] = {}
    # 循环处理：逐项遍历`payload.get('domains', [])`，把当前元素绑定到`domain`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for domain in payload.get("domains", []):
        # 条件门禁：判断`not isinstance(domain, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(domain, dict):
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue
        # 状态计算：把`str(domain.get('canonical_object', '')).strip()`的结果保存到`object_name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        object_name = str(domain.get("canonical_object", "")).strip()
        # 状态计算：把`{str(item.get('canonical_name', '')).strip() for item in domain.get('fields', []) if isinstance(ite…`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        fields = {
            str(item.get("canonical_name", "")).strip()
            for item in domain.get("fields", [])
            if isinstance(item, dict)
        }
        # 条件门禁：判断`object_name`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if object_name:
            # 显式调用：执行`objects.setdefault(object_name, set()).update((field for field in fields if field))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            objects.setdefault(object_name, set()).update(
                field for field in fields if field
            )
    # 结果返回：把`objects`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return objects


# 函数validate_contract：执行validate_contract对应的业务处理。
# - 输入：contract_path:str | Path、dictionary_path:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def validate_contract(
    contract_path: str | Path,
    dictionary_path: str | Path,
) -> dict[str, Any]:
    # 状态计算：把`load_contract(contract_path)`的结果保存到`contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract = load_contract(contract_path)
    # 状态计算：把`_load_yaml(Path(dictionary_path))`的结果保存到`dictionary_payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary_payload = _load_yaml(Path(dictionary_path))
    # 状态计算：把`str(dictionary_payload.get('dictionary_revision', ''))`的结果保存到`dictionary_revision`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary_revision = str(
        dictionary_payload.get("dictionary_revision", "")
    )
    # 状态计算：把`_dictionary_objects(Path(dictionary_path))`的结果保存到`objects`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    objects = _dictionary_objects(Path(dictionary_path))
    # 状态计算：把`[]`的结果保存到`issues`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    issues: list[dict[str, Any]] = []

    # 条件门禁：判断`contract.dictionary_revision != dictionary_revision`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if contract.dictionary_revision != dictionary_revision:
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DICTIONARY_REVISION_MISMATCH', 'expected': dictionary_revision, 'actual': contract.dictionary_…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "DICTIONARY_REVISION_MISMATCH",
                "expected": dictionary_revision,
                "actual": contract.dictionary_revision,
            }
        )

    # 状态计算：把`tuple(contract.datasets)`的结果保存到`dataset_ids`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_ids = tuple(contract.datasets)
    # 条件门禁：判断`len(dataset_ids) != len(REQUIRED_DATASETS) or set(dataset_ids) != set(REQUIRED_DATASETS)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if (
        len(dataset_ids) != len(REQUIRED_DATASETS)
        or set(dataset_ids) != set(REQUIRED_DATASETS)
    ):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DATASET_SET_MISMATCH', 'expected': REQUIRED_DATASETS, 'actual': dataset_ids})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "DATASET_SET_MISMATCH",
                "expected": REQUIRED_DATASETS,
                "actual": dataset_ids,
            }
        )

    # 状态计算：把`set(contract.raw.get('allowed_mapping_statuses', []))`的结果保存到`allowed`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    allowed = set(
        contract.raw.get("allowed_mapping_statuses", [])
    )
    # 条件门禁：判断`allowed != ALLOWED_STATUSES`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if allowed != ALLOWED_STATUSES:
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'ALLOWED_STATUS_SET_MISMATCH'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "ALLOWED_STATUS_SET_MISMATCH",
            }
        )

    # 循环处理：逐项遍历`contract.datasets.items()`，把当前元素绑定到`(dataset_id, dataset)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for dataset_id, dataset in contract.datasets.items():
        # 状态计算：把`str(dataset.get('canonical_object', ''))`的结果保存到`canonical_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        canonical_object = str(dataset.get("canonical_object", ""))
        # 状态计算：把`str(dataset.get('readiness', ''))`的结果保存到`readiness`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        readiness = str(dataset.get("readiness", ""))
        # 状态计算：把`dataset.get('mappings', [])`的结果保存到`mappings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        mappings = dataset.get("mappings", [])
        # 条件门禁：判断`readiness != 'READY_WITH_WARNING'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if readiness != "READY_WITH_WARNING":
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DATASET_NOT_READY_WITH_WARNING', 'dataset_id': dataset_id, 'readiness': readiness})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "DATASET_NOT_READY_WITH_WARNING",
                    "dataset_id": dataset_id,
                    "readiness": readiness,
                }
            )
        # 条件门禁：判断`canonical_object not in objects`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if canonical_object not in objects:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'CANONICAL_OBJECT_MISSING', 'dataset_id': dataset_id, 'canonical_object': canonical_object})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "CANONICAL_OBJECT_MISSING",
                    "dataset_id": dataset_id,
                    "canonical_object": canonical_object,
                }
            )
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue
        # 条件门禁：判断`not isinstance(mappings, list) or not mappings`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(mappings, list) or not mappings:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'MAPPINGS_MISSING', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "MAPPINGS_MISSING",
                    "dataset_id": dataset_id,
                }
            )
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue

        # 循环处理：逐项遍历`mappings`，把当前元素绑定到`mapping`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for mapping in mappings:
            # 状态计算：把`str(mapping.get('status', ''))`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = str(mapping.get("status", ""))
            # 状态计算：把`str(mapping.get('target', ''))`的结果保存到`target`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            target = str(mapping.get("target", ""))
            # 条件门禁：判断`status not in ALLOWED_STATUSES`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if status not in ALLOWED_STATUSES:
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'UNKNOWN_MAPPING_STATUS', 'dataset_id': dataset_id, 'target': target, 'status': status})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "UNKNOWN_MAPPING_STATUS",
                        "dataset_id": dataset_id,
                        "target": target,
                        "status": status,
                    }
                )
            # 条件门禁：判断`target not in objects[canonical_object]`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if target not in objects[canonical_object]:
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'TARGET_FIELD_NOT_IN_DICTIONARY', 'dataset_id': dataset_id, 'canonical_object': canonical_objec…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "TARGET_FIELD_NOT_IN_DICTIONARY",
                        "dataset_id": dataset_id,
                        "canonical_object": canonical_object,
                        "target": target,
                    }
                )

        # 条件门禁：判断`dataset_id == 'hq' and dataset.get('source_role') != 'SUPPLEMENTAL_RECONCILIATION'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset_id == "hq" and dataset.get("source_role") != "SUPPLEMENTAL_RECONCILIATION":
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'HQ_ROLE_NOT_SUPPLEMENTAL'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "HQ_ROLE_NOT_SUPPLEMENTAL",
                }
            )

        # 条件门禁：判断`dataset_id == 'kphq'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset_id == "kphq":
            # 状态计算：把`{str(item.get('target', '')): item for item in mappings}`的结果保存到`mapping_index`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            mapping_index = {
                str(item.get("target", "")): item
                for item in mappings
            }
            # 状态计算：把`mapping_index.get('snapshot_time', {})`的结果保存到`snapshot_time`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            snapshot_time = mapping_index.get("snapshot_time", {})
            # 状态计算：把`mapping_index.get('snapshot_time_precision', {})`的结果保存到`precision`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            precision = mapping_index.get(
                "snapshot_time_precision", {}
            )
            # 条件门禁：判断`snapshot_time.get('status') != 'NOT_APPLICABLE'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if snapshot_time.get("status") != "NOT_APPLICABLE":
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'AUCTION_TIME_MUST_REMAIN_NULL'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "AUCTION_TIME_MUST_REMAIN_NULL",
                    }
                )
            # 条件门禁：判断`precision.get('status') != 'CONSTANT' or precision.get('transform') != 'constant_DATE_ONLY'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if (
                precision.get("status") != "CONSTANT"
                or precision.get("transform")
                != "constant_DATE_ONLY"
            ):
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'AUCTION_TIME_PRECISION_NOT_DATE_ONLY'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "AUCTION_TIME_PRECISION_NOT_DATE_ONLY",
                    }
                )
            # 状态计算：把`str(dataset)`的结果保存到`serialized`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            serialized = str(dataset)
            # 循环处理：逐项遍历`('source_file_mtime_utc', 'ingested_at_utc', 'midnight', 'constant_09_25')`，把当前元素绑定到`forbidden`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for forbidden in (
                "source_file_mtime_utc",
                "ingested_at_utc",
                "midnight",
                "constant_09_25",
            ):
                # 条件门禁：判断`forbidden not in serialized`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if forbidden not in serialized:
                    # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'AUCTION_FORBIDDEN_FALLBACK_NOT_RECORDED', 'fallback': forbidden})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "AUCTION_FORBIDDEN_FALLBACK_NOT_RECORDED",
                            "fallback": forbidden,
                        }
                    )

        # 条件门禁：判断`dataset_id in CLASSIFICATION_DATASETS`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset_id in CLASSIFICATION_DATASETS:
            # 条件门禁：判断`canonical_object != 'ClassificationMarketSnapshot'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if canonical_object != "ClassificationMarketSnapshot":
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'CLASSIFICATION_OBJECT_WRONG', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "CLASSIFICATION_OBJECT_WRONG",
                        "dataset_id": dataset_id,
                    }
                )
            # 条件门禁：判断`'average_shares' not in dataset.get('source_extensions', [])`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if "average_shares" not in dataset.get(
                "source_extensions", []
            ):
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'UNCONFIRMED_AVERAGE_SHARES_NOT_EXTENSION', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "UNCONFIRMED_AVERAGE_SHARES_NOT_EXTENSION",
                        "dataset_id": dataset_id,
                    }
                )

        # 条件门禁：判断`dataset_id == 'zj' and dataset.get('sign_policy') != 'PRESERVE_SOURCE_SIGN'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset_id == "zj" and dataset.get("sign_policy") != "PRESERVE_SOURCE_SIGN":
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'MONEY_FLOW_SIGN_POLICY_INVALID'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "MONEY_FLOW_SIGN_POLICY_INVALID",
                }
            )

    # 状态计算：把`contract.raw.get('implemented_dictionary_changes', [])`的结果保存到`implemented`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    implemented = contract.raw.get(
        "implemented_dictionary_changes", []
    )
    # 状态计算：把`{str(item.get('change_id', '')) for item in implemented if isinstance(item, dict) and item.get('sta…`的结果保存到`implemented_ids`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    implemented_ids = {
        str(item.get("change_id", ""))
        for item in implemented
        if isinstance(item, dict)
        and item.get("status") == "IMPLEMENTED"
    }
    # 状态计算：把`{'ADD_CLASSIFICATION_MARKET_SNAPSHOT', 'AUCTION_TIME_PRECISION_GOVERNANCE'}`的结果保存到`required_ids`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    required_ids = {
        "ADD_CLASSIFICATION_MARKET_SNAPSHOT",
        "AUCTION_TIME_PRECISION_GOVERNANCE",
    }
    # 条件门禁：判断`not required_ids.issubset(implemented_ids)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not required_ids.issubset(implemented_ids):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'IMPLEMENTED_DICTIONARY_CHANGE_MISSING'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "IMPLEMENTED_DICTIONARY_CHANGE_MISSING",
            }
        )

    # 状态计算：把`[issue for issue in issues if issue['severity'] == 'ERROR']`的结果保存到`errors`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    errors = [
        issue for issue in issues
        if issue["severity"] == "ERROR"
    ]
    # 状态计算：把`sum((1 for item in contract.datasets.values() if item.get('readiness') == 'READY_WITH_WARNING'))`的结果保存到`ready_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ready_count = sum(
        1 for item in contract.datasets.values()
        if item.get("readiness") == "READY_WITH_WARNING"
    )
    # 状态计算：把`sum((1 for item in contract.datasets.values() if str(item.get('readiness', '')).startswith('BLOCKED…`的结果保存到`blocked_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    blocked_count = sum(
        1 for item in contract.datasets.values()
        if str(item.get("readiness", "")).startswith("BLOCKED_")
    )
    # 结果返回：把`{'task_id': 'TASK_017B', 'contract_version': contract.contract_version, 'dictionary_revision': dictionary_revision, 'da…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "task_id": "TASK_017B",
        "contract_version": contract.contract_version,
        "dictionary_revision": dictionary_revision,
        "dataset_count": len(contract.datasets),
        "ready_with_warning_count": ready_count,
        "blocked_count": blocked_count,
        "implemented_dictionary_change_count": len(implemented),
        "overall_status": "PASSED_WITH_WARNINGS" if not errors else "FAILED",
        "issues": issues,
    }
