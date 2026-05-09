import React, { useMemo } from 'react';
import { theme, colorOf, INDUSTRY_COLOR } from '../theme';
import { Pill } from './primitives/Pill';
import { formatNumber } from '../utils/format';

interface EnterpriseTop10Props {
  data: Array<Record<string, unknown>>;
  selectedDistrict?: string | null;
  selectedIndustry?: string | null;
}

/** 重点企业 Top 10 排行（按今日用电）。风险高的企业脉动闪烁。 */
export const EnterpriseTop10: React.FC<EnterpriseTop10Props> = ({
  data, selectedDistrict, selectedIndustry,
}) => {
  const top = useMemo(() => {
    let arr = data;
    if (selectedDistrict) arr = arr.filter((r) => r['区域'] === selectedDistrict);
    if (selectedIndustry) arr = arr.filter((r) => r['行业'] === selectedIndustry);

    // 取每个企业最新一天的记录
    const latestByName = new Map<string, Record<string, unknown>>();
    for (const r of arr) {
      const name = String(r['标题'] || '');
      const date = String(r['日期'] || '');
      const existing = latestByName.get(name);
      if (!existing || String(existing['日期'] || '') < date) {
        latestByName.set(name, r);
      }
    }
    return Array.from(latestByName.values())
      .sort((a, b) => Number(b['今日用电_MWh'] || 0) - Number(a['今日用电_MWh'] || 0))
      .slice(0, 10);
  }, [data, selectedDistrict, selectedIndustry]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ fontSize: 12, color: theme.textSecondary, marginBottom: 8 }}>
        重点企业用电 Top 10
        {(selectedDistrict || selectedIndustry) && (
          <span style={{ color: theme.textTertiary }}>
            {' · '}
            {[selectedDistrict, selectedIndustry].filter(Boolean).join(' / ')}
          </span>
        )}
      </div>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex',
                    flexDirection: 'column', gap: 4, paddingRight: 4 }}>
        {top.length === 0 && (
          <div style={{ color: theme.textTertiary, fontSize: 12,
                        textAlign: 'center', padding: 24 }}>
            无数据
          </div>
        )}
        {top.map((r, i) => {
          const risk = Number(r['风险指数'] || 0);
          const isHighRisk = risk >= 70;
          const power = Number(r['今日用电_MWh'] || 0);
          const maxPower = Number(top[0]['今日用电_MWh'] || 1);
          const widthPct = (power / maxPower) * 100;
          return (
            <div key={String(r['__id']) || i}
                 style={{
                   padding: '6px 8px',
                   borderRadius: 4,
                   background: isHighRisk
                     ? `${theme.danger}10`
                     : 'rgba(0, 217, 255, 0.04)',
                   border: `1px solid ${isHighRisk ? `${theme.danger}55` : theme.border}`,
                   animation: isHighRisk ? 'redPulse 2.5s ease-in-out infinite' : undefined,
                   position: 'relative',
                   overflow: 'hidden',
                 }}>
              {/* bar background */}
              <div style={{
                position: 'absolute', left: 0, top: 0, bottom: 0,
                width: `${widthPct}%`,
                background: `linear-gradient(90deg, ${theme.primary}11, ${theme.primary}33)`,
                pointerEvents: 'none',
              }} />
              <div style={{ position: 'relative', display: 'flex',
                            alignItems: 'center', gap: 8, fontSize: 11 }}>
                <span style={{
                  width: 18, color: theme.textTertiary, fontFamily: 'monospace',
                  textAlign: 'right',
                }}>
                  {(i + 1).toString().padStart(2, '0')}
                </span>
                <Pill label={String(r['行业'] || '')}
                      color={INDUSTRY_COLOR[String(r['行业'] || '')]}
                      size="sm" />
                <span style={{
                  flex: 1, color: theme.textPrimary, fontWeight: 500,
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                }}>
                  {String(r['标题'] || '')}
                </span>
                <span style={{ color: theme.primary, fontWeight: 600,
                               fontFamily: 'monospace' }}>
                  {formatNumber(power, { precision: 1 })} MW
                </span>
                <span style={{
                  color: isHighRisk ? theme.danger : theme.textTertiary,
                  fontSize: 10, minWidth: 32, textAlign: 'right',
                }}>
                  风险 {risk.toFixed(0)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
