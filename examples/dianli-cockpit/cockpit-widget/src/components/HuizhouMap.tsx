import React from 'react';
import { theme, colorOf, DISTRICT_COLOR } from '../theme';
import { HUIZHOU_DISTRICTS, MAP_VIEWBOX } from '../utils/geo';

interface HuizhouMapProps {
  /** 区域 → 用电量（用于亮度权重）。0-1 归一化值。 */
  intensity?: Record<string, number>;
  selected?: string | null;
  onSelect?: (district: string | null) => void;
}

/**
 * 惠州市 7 区简化 SVG 地图。
 * 每个区是一个圆角矩形，亮度 = 用电相对值，hover/click 高亮。
 */
export const HuizhouMap: React.FC<HuizhouMapProps> = ({
  intensity = {}, selected, onSelect,
}) => {
  return (
    <div style={{ width: '100%', height: '100%', display: 'flex',
                  flexDirection: 'column', position: 'relative' }}>
      <div style={{ fontSize: 12, color: theme.textSecondary,
                    marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>惠州市 · 区域用电热力</span>
        {selected && (
          <button onClick={() => onSelect?.(null)}
                  style={{ background: 'transparent',
                           border: `1px solid ${theme.border}`,
                           color: theme.primary, fontSize: 10, padding: '1px 8px',
                           borderRadius: 999, cursor: 'pointer' }}>
            取消选中 ✕
          </button>
        )}
      </div>
      <svg viewBox={MAP_VIEWBOX} style={{ width: '100%', flex: 1, maxHeight: '100%' }}
           preserveAspectRatio="xMidYMid meet">
        <defs>
          {HUIZHOU_DISTRICTS.map((d) => {
            const baseColor = colorOf(DISTRICT_COLOR[d.name]);
            return (
              <radialGradient key={d.name} id={`grad-${d.name}`} cx="50%" cy="50%">
                <stop offset="0%" stopColor={baseColor} stopOpacity="0.9" />
                <stop offset="100%" stopColor={baseColor} stopOpacity="0.25" />
              </radialGradient>
            );
          })}
        </defs>
        {HUIZHOU_DISTRICTS.map((d) => {
          const baseColor = colorOf(DISTRICT_COLOR[d.name]);
          const heat = intensity[d.name] ?? 0.5;
          const isSelected = selected === d.name;
          const opacity = 0.3 + heat * 0.7;
          return (
            <g key={d.name}
               onClick={() => onSelect?.(isSelected ? null : d.name)}
               style={{ cursor: 'pointer' }}>
              <rect
                x={d.x} y={d.y} width={d.width} height={d.height}
                rx={8} ry={8}
                fill={`url(#grad-${d.name})`}
                stroke={isSelected ? baseColor : `${baseColor}66`}
                strokeWidth={isSelected ? 2 : 1}
                style={{
                  opacity,
                  filter: isSelected ? `drop-shadow(0 0 10px ${baseColor})` : undefined,
                  transition: 'all 0.3s ease',
                }}
              />
              <text x={d.cx} y={d.cy} textAnchor="middle" dominantBaseline="middle"
                    fill={isSelected ? '#fff' : theme.textPrimary}
                    style={{
                      fontSize: 12, fontWeight: 600, letterSpacing: 0.5,
                      textShadow: `0 0 4px ${baseColor}`,
                      pointerEvents: 'none',
                      userSelect: 'none',
                    }}>
                {d.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
