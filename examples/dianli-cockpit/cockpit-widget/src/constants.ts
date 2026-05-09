/**
 * 7 张数据表的 datasheet ID（由 simulator/cli.py bootstrap 创建）
 *
 * 这些 ID 是 vika 私有部署里实际生成的。如果在另一个空间或重新建表，
 * 替换为新的 dst ID。生产场景应改成从 widget 设置面板可配置。
 */
export const DST_IDS = {
  industry: 'dst7WVffaqrqAgWjry',      // 电力驾驶舱_行业指标
  enterprise: 'dstcuEE4q5A5x0sSRU',    // 电力驾驶舱_重点企业
  loadCurve: 'dstjAj0Xsen9xuMYBZ',     // 电力驾驶舱_用电曲线
  alert: 'dstc8an2u4z0kYGUmk',         // 电力驾驶舱_预警事件
  renewable: 'dstEUPEfLnmYc8bAhf',     // 电力驾驶舱_新能源充电
  insight: 'dstJJdAAMgHvrzplvj',       // 电力驾驶舱_机器人洞察
  config: 'dstta2UbnmT1nvvqyE',        // 电力驾驶舱_配置参数
} as const;

export const DISTRICTS = [
  '惠城区', '惠阳区', '大亚湾区', '仲恺高新区',
  '博罗县', '惠东县', '龙门县',
] as const;

export const INDUSTRIES = [
  '电子信息', '石化能源', '装备制造',
  '汽车制造', '纺织食品', '新材料',
] as const;

// 多端断点
export const BREAKPOINT_MOBILE = 480;
export const BREAKPOINT_NARROW = 768;
export const BREAKPOINT_BIG_SCREEN = 1600;
