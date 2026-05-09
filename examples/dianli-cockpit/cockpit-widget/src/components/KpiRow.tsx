import React, { useMemo } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { KpiCard } from './KpiCard';
import { theme } from '../theme';

interface KpiRowProps {
  loadCurve: Array<Record<string, unknown>>;
  industry: Array<Record<string, unknown>>;
  alerts: Array<Record<string, unknown>>;
  enterprises: Array<Record<string, unknown>>;
  configKV: { getNumber: (k: string, fallback?: number) => number };
}

/**
 * 顶部 5 KPI：
 *  1. 今日总用电（MWh）—— sum 当前小时所有区
 *  2. 同比 —— industry 加权平均
 *  3. 平均景气指数
 *  4. 活跃预警（红+橙数）
 *  5. 在线企业 / 总数
 */
export const KpiRow: React.FC<KpiRowProps> = ({
  loadCurve, industry, alerts, enterprises, configKV,
}) => {
  const { isMobile, isNarrow } = useResponsive();

  // 1. 今日总用电（最近一小时全市求和）
  const totalLoadToday = useMemo(() => {
    if (!loadCurve.length) return 0;
    // 最大时间戳的所有记录
    const maxTs = loadCurve.reduce((acc, r) => {
      const t = String(r['时间戳'] || '');
      return t > acc ? t : acc;
    }, '');
    const latest = loadCurve.filter((r) => String(r['时间戳'] || '') === maxTs);
    // 换算累计：全市当前小时 ×24（粗略估算今日总）
    const sum = latest.reduce((acc, r) => acc + Number(r['累计用电_MWh'] || 0), 0);
    return Math.round(sum);
  }, [loadCurve]);

  const targetLoad = configKV.getNumber('KPI_今日总用电_目标', 30000);

  // 2. 行业加权同比平均
  const yoyAvg = useMemo(() => {
    if (!industry.length) return 0;
    let weighted = 0;
    let totalWeight = 0;
    for (const r of industry) {
      const w = Number(r['行业用电_MWh'] || 0);
      const yoy = Number(r['同比_%'] || 0);
      weighted += w * yoy;
      totalWeight += w;
    }
    return totalWeight ? weighted / totalWeight : 0;
  }, [industry]);

  // 3. 平均景气指数
  const avgProsperity = useMemo(() => {
    if (!industry.length) return 0;
    const sum = industry.reduce((acc, r) => acc + Number(r['景气指数'] || 0), 0);
    return sum / industry.length;
  }, [industry]);

  // 4. 活跃预警（处理中或已纳入监测）
  const activeAlerts = useMemo(() => {
    return alerts.filter((r) => {
      const s = String(r['状态'] || '');
      return s === '处理中' || s === '已纳入监测';
    });
  }, [alerts]);
  const redCount = activeAlerts.filter((r) => r['等级'] === '红色').length;
  const orangeCount = activeAlerts.filter((r) => r['等级'] === '橙色').length;
  const alertWarn = redCount >= 3;

  // 5. 在线企业（最近 1 天有记录的企业数）
  const enterpriseCount = useMemo(() => {
    return new Set(enterprises.map((r) => String(r['标题'] || ''))).size;
  }, [enterprises]);

  const cards = [
    <KpiCard
      key="load" label="今日总用电"
      value={totalLoadToday} unit="MWh" precision={0}
      delta={`目标 ${targetLoad.toLocaleString('zh-CN')} MWh`}
      deltaColor={totalLoadToday >= targetLoad ? theme.success : theme.warning}
      badge="实时" badgePulse
      compact={isMobile}
    />,
    <KpiCard
      key="yoy" label="平均同比"
      value={yoyAvg} unit="%" precision={1}
      delta={yoyAvg >= 0 ? '同比正向 ▲' : '同比负向 ▼'}
      deltaColor={yoyAvg >= 0 ? theme.success : theme.danger}
      compact={isMobile}
    />,
    <KpiCard
      key="prosperity" label="景气指数"
      value={avgProsperity} precision={1}
      delta={`警戒线 ${configKV.getNumber('KPI_平均景气指数_警戒线', 50)}`}
      deltaColor={avgProsperity >= configKV.getNumber('KPI_平均景气指数_警戒线', 50)
                  ? theme.success : theme.danger}
      compact={isMobile}
    />,
    <KpiCard
      key="alerts" label="活跃预警"
      value={activeAlerts.length} precision={0}
      delta={`红 ${redCount} / 橙 ${orangeCount}`}
      deltaColor={alertWarn ? theme.danger : theme.warning}
      warning={alertWarn}
      badge={alertWarn ? '高危' : undefined}
      badgePulse={alertWarn}
      compact={isMobile}
    />,
    <KpiCard
      key="enterprises" label="重点企业"
      value={enterpriseCount} precision={0}
      delta={`总跟踪`}
      compact={isMobile}
    />,
  ];

  const gridCols = isMobile ? 'repeat(2, 1fr)' :
                   isNarrow ? 'repeat(3, 1fr)' : 'repeat(5, 1fr)';

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: gridCols,
      gap: 10,
      padding: '12px 16px',
    }}>
      {cards}
    </div>
  );
};
