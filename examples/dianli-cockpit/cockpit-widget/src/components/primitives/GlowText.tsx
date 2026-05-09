import React from 'react';
import { theme } from '../../theme';

interface GlowTextProps {
  children: React.ReactNode;
  color?: string;
  size?: number;
  weight?: number | string;
  letterSpacing?: number;
  style?: React.CSSProperties;
}

/** 霓虹光晕的发光数字/文字。用于 KPI 数字、标题等高亮元素。 */
export const GlowText: React.FC<GlowTextProps> = ({
  children, color = theme.primary, size = 32, weight = 700, letterSpacing = 1, style,
}) => (
  <span
    style={{
      color,
      fontSize: size,
      fontWeight: weight as React.CSSProperties['fontWeight'],
      letterSpacing,
      textShadow: theme.glowText(color),
      fontFeatureSettings: '"tnum"',  // tabular numerals so jitter doesn't reflow
      ...style,
    }}
  >
    {children}
  </span>
);
