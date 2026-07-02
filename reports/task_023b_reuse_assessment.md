# TASK_023B 复用优先审查

## 结论

TASK_023B不新造包管理、注册表查询或Python环境管理框架。实现优先复用Python标准库和Windows既有系统接口，只补充本项目需要的供应商无关证据合同、隐私边界和候选排序。

## 复用项

- `importlib.util.find_spec`：只判断模块入口存在，不导入供应商SDK；
- `py -0p`、PATH与`VIRTUAL_ENV`：发现明确可用的Python解释器，不进行全盘扫描；
- Windows卸载注册表：读取已安装程序的名称、版本和发布者；
- `shutil.which`：检查规则中明确列出的可执行入口；
- `json`与项目现有TASK_023A清单：延续稳定数据合同。

## 不直接引入第三方依赖的原因

本任务只是离线环境盘点。引入WMI、第三方注册表库、包管理框架或供应商SDK会扩大依赖和安全面，也无法提高当前证据质量。Python标准库已覆盖需求。

## 最小自研范围

- Provider与Windows证据规则映射；
- 证据分层和确定性评分；
- 交易执行Provider自动排除；
- 不记录秘密值、安装路径和账户信息的报告合同。

## 后续替换边界

若未来采用企业级资产盘点工具，只需把其结果转换为`PythonInterpreterEvidence`和`InstalledApplicationEvidence`，上层评分、报告和TASK_023C接口无需重写。
