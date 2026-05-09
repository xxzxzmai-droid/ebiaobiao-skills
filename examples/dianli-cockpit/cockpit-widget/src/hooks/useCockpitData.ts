import { useMemo } from 'react';
import { useDatasheet, useRecords } from '@apitable/widget-sdk';
import { DST_IDS } from '../constants';

/** 一条记录的字段值（从 record.getCellValue 获取后归一化的对象） */
type Row = Record<string, unknown>;

/**
 * 包装 7 张表的读取，把 widget-sdk 的 record 对象归一化成 plain object。
 *
 * widget-sdk hooks 必须**在 widget 里**调用（有 React context），
 * 因此本 hook 是组件层的入口。
 */
export function useCockpitData() {
  const industryDs = useDatasheet(DST_IDS.industry);
  const enterpriseDs = useDatasheet(DST_IDS.enterprise);
  const loadCurveDs = useDatasheet(DST_IDS.loadCurve);
  const alertDs = useDatasheet(DST_IDS.alert);
  const renewableDs = useDatasheet(DST_IDS.renewable);
  const insightDs = useDatasheet(DST_IDS.insight);
  const configDs = useDatasheet(DST_IDS.config);

  // useRecords 的 2 参版本：(datasheet, viewId)
  const industryRecs = useRecords(industryDs, undefined);
  const enterpriseRecs = useRecords(enterpriseDs, undefined);
  const loadCurveRecs = useRecords(loadCurveDs, undefined);
  const alertRecs = useRecords(alertDs, undefined);
  const renewableRecs = useRecords(renewableDs, undefined);
  const insightRecs = useRecords(insightDs, undefined);
  const configRecs = useRecords(configDs, undefined);

  const industry = useMemo(() => normalize(industryRecs), [industryRecs]);
  const enterprise = useMemo(() => normalize(enterpriseRecs), [enterpriseRecs]);
  const loadCurve = useMemo(() => normalize(loadCurveRecs), [loadCurveRecs]);
  const alert = useMemo(() => normalize(alertRecs), [alertRecs]);
  const renewable = useMemo(() => normalize(renewableRecs), [renewableRecs]);
  const insight = useMemo(() => normalize(insightRecs), [insightRecs]);
  const config = useMemo(() => normalize(configRecs), [configRecs]);

  const ready = !!(industryDs && enterpriseDs && loadCurveDs && alertDs &&
                   renewableDs && insightDs && configDs);

  return {
    ready,
    industry,
    enterprise,
    loadCurve,
    alert,
    renewable,
    insight,
    config,
    // 也暴露 datasheet 对象（widget 可能需要 checkPermission 或 setRecords）
    datasheets: {
      industry: industryDs,
      enterprise: enterpriseDs,
      loadCurve: loadCurveDs,
      alert: alertDs,
      renewable: renewableDs,
      insight: insightDs,
      config: configDs,
    },
  };
}

function normalize(records: ReturnType<typeof useRecords> | undefined): Row[] {
  if (!records) return [];
  return records.map((r) => {
    // record 对象有 getCellValue(fieldName)，遍历 fields 取值
    const fields: Row = { __id: r.id };
    // record 有 fieldsKeyByName（field name → value） — 但根据 sdk 版本不一定可用
    // 用 record.getCellValuesByName() 兼容更广
    try {
      const all = (r as any).getCellValuesByName ? (r as any).getCellValuesByName() : null;
      if (all) Object.assign(fields, all);
    } catch {
      // ignore
    }
    return fields;
  });
}
