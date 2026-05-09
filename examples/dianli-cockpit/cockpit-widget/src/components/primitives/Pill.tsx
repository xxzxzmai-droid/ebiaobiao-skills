import React from 'react';
import { colorOf } from '../../theme';

interface PillProps {
  label: string;
  color?: string;          // vika color name OR hex
  size?: 'sm' | 'md';
  onClick?: () => void;
  active?: boolean;
}

/** 彩虹标签胶囊：状态/区域/行业/标签字段渲染。 */
export const Pill: React.FC<PillProps> = ({ label, color, size = 'md', onClick, active }) => {
  const fg = colorOf(color);
  const bg = `${fg}22`;        // 13% 透明
  const border = active ? fg : `${fg}66`;
  const padY = size === 'sm' ? 2 : 4;
  const padX = size === 'sm' ? 8 : 10;
  const fs = size === 'sm' ? 11 : 12;
  return (
    <span
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        backgroundColor: bg,
        color: fg,
        padding: `${padY}px ${padX}px`,
        borderRadius: 999,
        fontSize: fs,
        fontWeight: 600,
        lineHeight: 1.2,
        whiteSpace: 'nowrap',
        border: `1px solid ${border}`,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.15s ease',
        boxShadow: active ? `0 0 8px ${fg}66` : 'none',
        userSelect: 'none',
      }}
    >
      {label}
    </span>
  );
};
