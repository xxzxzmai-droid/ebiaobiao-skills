/**
 * 惠州市 7 区简化几何（mosaic 风格）
 *
 * 不追求地理精确——大屏风格里通常用风格化形状代表区域。
 * SVG viewBox 0 0 400 300。每区一个圆角矩形，按惠州大致地理排布。
 *
 * 真实地理数据可从 https://datav.aliyun.com/portal/school/atlas/area_selector
 * 拿到 GeoJSON 然后用工具转成 SVG path。这里用 mosaic 是为了让 demo 立刻能跑、
 * 且大屏调性下其实更好看。
 */
export interface DistrictShape {
  name: string;
  // SVG <rect> 样式坐标
  x: number;
  y: number;
  width: number;
  height: number;
  // 中心点（标签位置）
  cx: number;
  cy: number;
}

export const HUIZHOU_DISTRICTS: DistrictShape[] = [
  // 北边
  { name: '龙门县', x: 60, y: 20, width: 110, height: 60, cx: 115, cy: 50 },
  { name: '博罗县', x: 180, y: 20, width: 160, height: 80, cx: 260, cy: 60 },
  // 中间
  { name: '惠城区', x: 130, y: 110, width: 100, height: 70, cx: 180, cy: 145 },
  { name: '仲恺高新区', x: 50, y: 90, width: 70, height: 90, cx: 85, cy: 135 },
  { name: '惠东县', x: 240, y: 110, width: 130, height: 90, cx: 305, cy: 155 },
  // 南边
  { name: '惠阳区', x: 100, y: 200, width: 130, height: 70, cx: 165, cy: 235 },
  { name: '大亚湾区', x: 240, y: 210, width: 110, height: 60, cx: 295, cy: 240 },
];

export const MAP_VIEWBOX = '0 0 400 300';
