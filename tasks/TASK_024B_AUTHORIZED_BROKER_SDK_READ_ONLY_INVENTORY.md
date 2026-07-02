# TASK_024B：用户已授权券商SDK包与只读行情能力盘点

状态：IMPLEMENTED_PENDING_WINDOWS_EVIDENCE

## 一、当前位置

```text
P0 复用优先与官方来源门禁
        ↓
TASK_024A 官方交易所与券商接口基线：已完成
        ↓
TASK_024A1 教学式注释前置门禁整改：已完成
        ↓
>>> TASK_024B 用户已授权券商SDK与只读能力盘点：当前位置
        ↓
TASK_024C 首个已授权券商只读Provider薄适配：仅在24B产生READY候选后启动
```

## 二、目标

基于用户明确提供的官方券商客户端、SDK安装包、开发文档和非秘密授权事实，确定是否存在可以合法进入只读行情薄适配的券商Provider。

TASK_024B不负责安装SDK、申请账户、登录、联网探测、发送订单或激活交易能力。

## 三、首批官方候选

1. 中国银河证券星耀数智与TFast；
2. 中泰证券XTP Quote/Level2；
3. 国信证券iQuant当前客户端；
4. 广发证券投易通当前官方组件；
5. 后续由官方资料和用户真实授权补充的其他券商。

目录排序不代表用户已经获得授权，也不代表某产品必然提供独立公开SDK。

## 四、四道不可替代的准入门禁

```text
本地官方SDK、客户端或开发文档证据
+ 用户明确确认合法授权
+ 用户明确确认只读行情权限
+ 交易域不存在，或已经确认与行情域隔离
= READY_FOR_READ_ONLY_ADAPTER_TASK
```

评分只能用于候选排序，不能绕过任何一道门禁。

## 五、隐私和安全边界

- 只扫描用户明确指定的专用证据目录；
- 禁止整盘扫描；
- 不读取SDK二进制、压缩包或文档内容；
- 报告只保存命中的文件基名和匿名根标签；
- 不保存绝对路径；
- 不接受账号、密码、Token、API Key、用户ID、服务器地址、IP或端口字段；
- 不导入券商SDK；
- 不创建行情或交易会话；
- 不联网；
- 不写注册表、数据库或券商客户端；
- 不发送订单。

## 六、输出状态

### 1. 找到完整候选

```text
selection_status = AUTHORIZED_READ_ONLY_CANDIDATES_FOUND
next_task = TASK_024C_FIRST_AUTHORIZED_BROKER_READ_ONLY_ADAPTER
```

### 2. 找到本地包或客户端，但授权信息不完整

```text
selection_status = LOCAL_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION
next_task = TASK_024B_AUTHORIZATION_EVIDENCE_COMPLETION
```

### 3. 没有找到已授权券商SDK证据

```text
selection_status = NO_AUTHORIZED_BROKER_SDK_EVIDENCE
next_task = TASK_024B_AUTHORIZED_SDK_EVIDENCE_INTAKE
```

第三种是正常盘点结果，不会自动降级选择AKShare、Tushare或未验证爬取接口。

## 七、交付

- `configs/providers/broker_sdk_inventory_rules_v1.json`；
- `configs/providers/broker_sdk_authorization_evidence_v1.example.json`；
- `src/a_stock_quant/broker_sdk_inventory.py`；
- `scripts/run_task_024b_broker_sdk_inventory.py`；
- `tests/test_broker_sdk_inventory.py`；
- 本机UTF-8 JSON盘点报告；
- 架构图、项目状态和多源适配架构当前位置更新；
- 教学式前置注释回归门禁扩展。
