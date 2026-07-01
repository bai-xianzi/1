# 本脚本核心功能：验证任务018b数据就绪度证据的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    sys.path.insert(0, str(root / 'src'))

    from a_stock_quant.data_contracts import QualityStatus
    from a_stock_quant.data_readiness import DataReadinessEngine, ReadinessStatus, load_data_readiness_policy
    from a_stock_quant.data_readiness_evidence import StandardQueryEvidenceBuilder, StandardQueryReadinessService, load_evidence_rule_config
    from a_stock_quant.standard_data_service import ProviderDescriptor, StandardDataQuery, StandardDataRecord, StandardDataUsage, StandardQueryMetadata, StandardQueryResult

    policy = load_data_readiness_policy(root/'configs/quality/data_readiness_policy_v0.json')
    rules = load_evidence_rule_config(root/'configs/quality/data_readiness_evidence_rules_v0.json')
    service = StandardQueryReadinessService(DataReadinessEngine(policy), StandardQueryEvidenceBuilder(rules))
    current_warning = 0
    historical_block = 0
    rows = []
    # 循环处理：将 `policy.dataset_catalog` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in policy.dataset_catalog:
        object_name = item.canonical_objects[0]
        selector = '000001' if item.selector_mode == 'INSTRUMENT_ID' else 'SOURCE_VENDOR:NODE:1'
        query = StandardDataQuery(item.dataset_id, object_name, (selector,) if item.selector_mode == 'INSTRUMENT_ID' else (), date(2026,6,27), date(2026,6,27), entity_ids=(selector,) if item.selector_mode == 'ENTITY_ID' else (), as_of_date=date(2026,6,27))
        key_name = 'instrument_id' if item.selector_mode == 'INSTRUMENT_ID' else 'node_id'
        record = StandardDataRecord(object_name, {key_name:selector,'trade_date':date(2026,6,27)}, {key_name:selector,'trade_date':date(2026,6,27)}, f'{item.dataset_id}:1', {}, (), ({'canonical_field':key_name,'source_fields':[key_name]},))
        descriptor = ProviderDescriptor(item.provider_id,item.dataset_id,item.canonical_objects,'coverage-v1','mapping-v1','0.6.0',item.selector_mode)
        metadata = StandardQueryMetadata(item.dataset_id,object_name,item.provider_id,'coverage-v1','mapping-v1','0.6.0',1,1,QualityStatus.PASSED,False,(),{},1)
        standard_result = StandardQueryResult(query,metadata,(record,))
        current = service.assess(standard_result,descriptor)
        # 条件分支：检查 `current.decision.status is ReadinessStatus.WARNING` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if current.decision.status is ReadinessStatus.WARNING: current_warning += 1
        historical_query = StandardDataQuery(item.dataset_id, object_name, (selector,) if item.selector_mode == 'INSTRUMENT_ID' else (), date(2026,6,27), date(2026,6,27), entity_ids=(selector,) if item.selector_mode == 'ENTITY_ID' else (), as_of_date=date(2026,6,27), usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST)
        historical = service.assess(StandardQueryResult(historical_query,metadata,(record,)),descriptor)
        # 条件分支：检查 `historical.decision.status is ReadinessStatus.BLOCKED` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if historical.decision.status is ReadinessStatus.BLOCKED: historical_block += 1
        rows.append({'dataset_id':item.dataset_id,'current_status':current.decision.status.value,'historical_status':historical.decision.status.value,'evidence_count':len(current.evidence)})
    issues = []
    # 条件分支：检查 `current_warning != len(policy.dataset_catalog)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if current_warning != len(policy.dataset_catalog): issues.append('当前快照研究未全部产生WARNING。')
    # 条件分支：检查 `historical_block != len(policy.dataset_catalog)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if historical_block != len(policy.dataset_catalog): issues.append('严格历史用途未全部阻断。')
    # 条件分支：检查 `any((row['evidence_count'] != 8 for row in rows))` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if any(row['evidence_count'] != 8 for row in rows): issues.append('存在证据维度不完整的数据集。')
    report = {'task_id':'TASK_018B','adapter_version':'0.1.0','rules_version':rules.rules_version,'dataset_count':len(rows),'evidence_dimension_count':8,'current_snapshot_warning_count':current_warning,'strict_historical_block_count':historical_block,'database_connection_attempted':False,'write_operation_count':0,'overall_status':'PASSED' if not issues else 'FAILED','issues':issues,'datasets':rows}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    # 输出结果：返回 `0 if not issues else 1` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if not issues else 1

# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == '__main__': raise SystemExit(main())
