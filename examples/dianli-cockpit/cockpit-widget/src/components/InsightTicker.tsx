import React from 'react';
import { theme, colorOf, DISTRICT_COLOR } from '../theme';

interface InsightTickerProps {
  data: Array<Record<string, unknown>>;
}

/** 底部跑马灯：机器人洞察滚动展示。 */
export const InsightTicker: React.FC<InsightTickerProps> = ({ data }) => {
  if (!data.length) return null;

  // CSS @keyframes marquee 在 style.css 里，width 根据条目数估算
  const items = data.slice(0, 20);

  return (
    <div style={{
      borderTop: `1px solid ${theme.border}`,
      background: 'rgba(0, 217, 255, 0.04)',
      overflow: 'hidden',
      whiteSpace: 'nowrap',
      padding: '6px 0',
      position: 'relative',
    }}>
      <div style={{
        display: 'inline-flex',
        gap: 40,
        animation: 'marquee 60s linear infinite',
        paddingLeft: '100%',
        whiteSpace: 'nowrap',
      }}>
        {[...items, ...items].map((r, i) => {
          const district = String(r['区域'] || '');
          const itype = String(r['类型'] || '');
          const content = String(r['洞察内容'] || '');
          return (
            <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
                                    fontSize: 12, color: theme.textSecondary }}>
              <span style={{ color: colorOf(DISTRICT_COLOR[district]),
                              fontWeight: 600 }}>● {district}</span>
              <span style={{ color: theme.primary }}>[{itype}]</span>
              <span>{content}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};
