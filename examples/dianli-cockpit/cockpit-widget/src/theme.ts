// 大屏驾驶舱主题（固定深色，不跟随 vika）
export const theme = {
  // 底色
  bg: '#0A1929',
  bgPanel: 'rgba(15, 31, 53, 0.85)',
  bgPanelSolid: '#0F1F35',
  // 边框
  border: 'rgba(0, 217, 255, 0.18)',
  borderStrong: 'rgba(0, 217, 255, 0.4)',
  // 主色
  primary: '#00D9FF',          // 霓虹青（主强调）
  primarySoft: 'rgba(0, 217, 255, 0.15)',
  warning: '#FF6B35',          // 警示橙
  success: '#00FF94',          // 正向绿
  danger: '#FF3D5F',           // 红色预警
  gold: '#FFD700',             // 金（评级、KPI 高亮）
  // 文字
  textPrimary: '#FFFFFF',
  textSecondary: '#8AA1B6',
  textTertiary: '#5C7290',
  // 渐变
  gradientPanel: 'linear-gradient(135deg, rgba(0,217,255,0.08), rgba(0,217,255,0.02))',
  gradientPrimary: 'linear-gradient(135deg, #00D9FF, #00FF94)',
  // 阴影/光晕
  glow: (color: string, blur = 8) => `drop-shadow(0 0 ${blur}px ${color})`,
  glowText: (color: string) => `0 0 8px ${color}, 0 0 16px ${color}40`,
};

// 区域 / 行业 / 状态色名 → hex（同 simulator/shared/constants.py 但前端独立维护）
export const COLORS = {
  // vika SingleSelect color name → hex
  gray: '#8AA1B6',
  red: '#FF3D5F',
  orange: '#FF6B35',
  yellow: '#FFD700',
  green: '#00FF94',
  cyan: '#00D9FF',
  blue: '#3B82F6',
  purple: '#A855F7',
  pink: '#EC4899',
  brown: '#A16207',
  dustRed: '#9F1239',
  lime: '#84CC16',
  magenta: '#D946EF',
  geekBlue: '#1E3A8A',
  gold: '#FACC15',
  volcano: '#C2410C',
};

export type ColorName = keyof typeof COLORS;

export const DISTRICT_COLOR: Record<string, ColorName> = {
  '惠城区': 'blue',
  '惠阳区': 'green',
  '大亚湾区': 'cyan',
  '仲恺高新区': 'purple',
  '博罗县': 'orange',
  '惠东县': 'red',
  '龙门县': 'yellow',
};

export const INDUSTRY_COLOR: Record<string, ColorName> = {
  '电子信息': 'cyan',
  '石化能源': 'red',
  '装备制造': 'blue',
  '汽车制造': 'orange',
  '纺织食品': 'green',
  '新材料': 'purple',
};

export const ALERT_LEVEL_COLOR: Record<string, ColorName> = {
  '红色': 'red',
  '橙色': 'orange',
  '黄色': 'yellow',
};

export const ALERT_STATUS_COLOR: Record<string, ColorName> = {
  '处理中': 'red',
  '已纳入监测': 'orange',
  '已闭环': 'green',
  '已忽略': 'gray',
};

export function colorOf(name: string | undefined, fallback: ColorName = 'gray'): string {
  if (!name) return COLORS[fallback];
  // 直接是 hex
  if (name.startsWith('#')) return name;
  return (COLORS as Record<string, string>)[name] || COLORS[fallback];
}
