import React, { useEffect, useState } from 'react';
import { theme } from '../theme';
import { Pill } from './primitives/Pill';
import { PulseDot } from './primitives/PulseDot';

interface HeaderBarProps {
  title?: string;
  filterDistrict?: string | null;
  filterIndustry?: string | null;
  onResetFilter?: () => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  title = '惠州市电力看经济 · 实时驾驶舱',
  filterDistrict, filterIndustry, onResetFilter,
}) => {
  const clock = useClock();
  const hasFilter = !!(filterDistrict || filterIndustry);

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px',
      borderBottom: `1px solid ${theme.border}`,
      background: theme.gradientPanel,
    }}>
      <PulseDot color={theme.primary} size={10} />
      <h1 style={{
        margin: 0, fontSize: 18, fontWeight: 700, letterSpacing: 1,
        color: theme.textPrimary, textShadow: theme.glowText(theme.primary),
      }}>
        {title}
      </h1>
      <div style={{ flex: 1 }} />
      {hasFilter && (
        <>
          {filterDistrict && <Pill label={`区域：${filterDistrict}`} color="cyan" size="sm" />}
          {filterIndustry && <Pill label={`行业：${filterIndustry}`} color="orange" size="sm" />}
          <button onClick={onResetFilter}
                  style={{
                    background: 'transparent',
                    border: `1px solid ${theme.border}`,
                    color: theme.textSecondary, fontSize: 11,
                    padding: '3px 10px', borderRadius: 999, cursor: 'pointer',
                  }}>
            重置过滤 ✕
          </button>
        </>
      )}
      <span style={{
        fontSize: 14, color: theme.primary, letterSpacing: 1,
        fontFeatureSettings: '"tnum"',
        textShadow: theme.glowText(theme.primary),
      }}>
        {clock}
      </span>
    </div>
  );
};

function useClock() {
  const [t, setT] = useState(() => formatNow());
  useEffect(() => {
    const id = setInterval(() => setT(formatNow()), 1000);
    return () => clearInterval(id);
  }, []);
  return t;
}

function formatNow() {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
         `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
