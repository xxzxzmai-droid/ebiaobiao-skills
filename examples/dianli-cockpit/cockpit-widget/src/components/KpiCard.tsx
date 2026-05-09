import React, { useEffect, useRef, useState } from 'react';
import { theme } from '../theme';
import { GlowText } from './primitives/GlowText';
import { PulseDot } from './primitives/PulseDot';

interface KpiCardProps {
  label: string;
  value: number;
  unit?: string;
  precision?: number;
  /** 同比 / 副指标，已格式化的字符串如 '+4.7%' */
  delta?: string;
  deltaColor?: string;          // theme.success / theme.danger
  /** 顶部小标签（如"实时"+脉动） */
  badge?: string;
  badgePulse?: boolean;
  warning?: boolean;            // 警戒态——边框泛红
  compact?: boolean;
}

/** 数字 counter 跳变的 KPI 卡片。500ms 缓动。 */
export const KpiCard: React.FC<KpiCardProps> = ({
  label, value, unit, precision = 0, delta, deltaColor = theme.success,
  badge, badgePulse, warning, compact,
}) => {
  const display = useCounter(value, 500);
  const fontSize = compact ? 24 : 36;
  return (
    <div
      style={{
        background: theme.gradientPanel,
        border: `1px solid ${warning ? theme.danger : theme.border}`,
        boxShadow: warning ? `inset 0 0 16px ${theme.danger}33` : 'none',
        borderRadius: 8,
        padding: compact ? '12px 14px' : '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        position: 'relative',
        overflow: 'hidden',
        minHeight: compact ? 80 : 100,
      }}
    >
      {/* 顶部 label + 实时徽标 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 12, color: theme.textSecondary, fontWeight: 500 }}>
          {label}
        </span>
        {badge && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4,
                         marginLeft: 'auto', fontSize: 10, color: theme.textTertiary }}>
            {badgePulse && <PulseDot color={theme.success} size={6} />}
            {badge}
          </span>
        )}
      </div>
      {/* 主数字 */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 'auto' }}>
        <GlowText size={fontSize} color={warning ? theme.danger : theme.primary}>
          {Number.isFinite(display) ? display.toFixed(precision) : '—'}
        </GlowText>
        {unit && (
          <span style={{ fontSize: 12, color: theme.textSecondary, fontWeight: 500 }}>
            {unit}
          </span>
        )}
      </div>
      {/* 副指标 */}
      {delta && (
        <span style={{ fontSize: 11, color: deltaColor, fontWeight: 600, letterSpacing: 0.3 }}>
          {delta}
        </span>
      )}
    </div>
  );
};

/** 数字平滑过渡 hook —— 每 step ms 走一帧 */
function useCounter(target: number, durationMs = 500): number {
  const [val, setVal] = useState(target);
  const fromRef = useRef(target);
  const startRef = useRef(0);

  useEffect(() => {
    fromRef.current = val;
    startRef.current = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - startRef.current) / durationMs);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      const next = fromRef.current + (target - fromRef.current) * eased;
      setVal(next);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, durationMs]);

  return val;
}
