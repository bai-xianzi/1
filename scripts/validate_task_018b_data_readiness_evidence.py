from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys


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
        if current.decision.status is ReadinessStatus.WARNING: current_warning += 1
        historical_query = StandardDataQuery(item.dataset_id, object_name, (selector,) if item.selector_mode == 'INSTRUMENT_ID' else (), date(2026,6,27), date(2026,6,27), entity_ids=(selector,) if item.selector_mode == 'ENTITY_ID' else (), as_of_date=date(2026,6,27), usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST)
        historical = service.assess(StandardQueryResult(historical_query,metadata,(record,)),descriptor)
        if historical.decision.status is ReadinessStatus.BLOCKED: historical_block += 1
        rows.append({'dataset_id':item.dataset_id,'current_status':current.decision.status.value,'historical_status':historical.decision.status.value,'evidence_count':len(current.evidence)})
    issues = []
    if current_warning != len(policy.dataset_catalog): issues.append('当前快照研究未全部产生WARNING。')
    if historical_block != len(policy.dataset_catalog): issues.append('严格历史用途未全部阻断。')
    if any(row['evidence_count'] != 8 for row in rows): issues.append('存在证据维度不完整的数据集。')
    report = {'task_id':'TASK_018B','adapter_version':'0.1.0','rules_version':rules.rules_version,'dataset_count':len(rows),'evidence_dimension_count':8,'current_snapshot_warning_count':current_warning,'strict_historical_block_count':historical_block,'database_connection_attempted':False,'write_operation_count':0,'overall_status':'PASSED' if not issues else 'FAILED','issues':issues,'datasets':rows}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if not issues else 1

if __name__ == '__main__': raise SystemExit(main())
