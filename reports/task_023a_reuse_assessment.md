# TASK_023A 复用优先审查

## 结论

TASK_023A 不重新实现任何供应商SDK，也不尝试仿造商业接口。它只建设供应商无关的离线发现层，并复用Python标准库的 `importlib.util.find_spec`、`platform` 和 `os.environ` 完成环境盘点。

## 已核实的官方或官方项目入口

| Provider | 可安全探测的Python模块 | 证据 | 当前处理 |
|---|---|---|---|
| Wind | `WindPy` | Wind Client API及Wind官方Wrapper | 只做模块入口发现 |
| 同花顺iFinD | `iFinDPy` | 同花顺数据接口官方Python示例 | 只做模块入口发现 |
| Tushare Pro | `tushare` | Tushare官方安装与SDK文档 | 只做模块和Token引用名称发现 |
| AKShare | `akshare` | AKShare官方项目与安装文档 | 只做模块入口发现 |

## 暂不填写模块名的目标

Choice、银河证券星耀数智、QMT、PTrade和交易所/监管来源在本任务中没有获得足够统一、稳定且与用户实际版本一致的Python模块证据，因此保持人工或逐来源审查。

## 自研最小范围

只自研以下项目独有的治理部分：

- 供应商无关发现报告格式；
- 不记录秘密值的安全边界；
- 排除交易执行Provider自动推荐；
- 下一步候选排序；
- 与项目Provider、Canonical、Readiness架构的衔接。

不会自研：

- 厂商登录协议；
- 厂商数据接口；
- 券商下单协议；
- HTTP抓取框架；
- SDK安装器。

## 可复核来源

- Wind Client API：https://www.wind.com.cn/mobile/ClientApi/en.html
- Wind官方Python Wrapper：https://github.com/WindQuant/Official/blob/master/WAPIWrapper/WAPIWrapperPython/WindPy.py
- 同花顺iFinD Python示例：https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/quantapi-web/example.html
- 同花顺iFinD环境部署说明：https://quantapi.10jqka.com.cn/gwstatic/static/ds_web/quantapi-web/help-center/deploy.html
- Tushare Python SDK：https://tushare.pro/document/1?doc_id=131
- AKShare官方项目：https://github.com/akfamily/akshare
- AKShare安装说明：https://akshare.akfamily.xyz/installation.html
