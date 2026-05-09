/**
 * 7 张数据表的 datasheet ID（由 simulator/cli.py bootstrap 创建）
 *
 * **本仓库不提交真实 dst ID**（虽然 dst id 离开 token 没用，但避免无意识泄漏）。
 * 把 placeholder 换成你自己 vika 里 bootstrap 后产生的 ID。
 *
 * 怎么找：
 *   python3 ~/.codex/skills/ebiaobiao-fusion-api/scripts/ebiao_fusion.py search-nodes \
 *     --query 电力驾驶舱 --type Datasheet
 * 把返回的 7 张表 id 复制到这里。或读 ~/.dianli-cockpit-dst.json 之类的本地文件。
 *
 * 也可以改成从 widget 设置面板（useSettingsButton + useCloudStorage）配置。
 */
export const DST_IDS = {
  industry: 'dstREPLACE_INDUSTRY',      // 电力驾驶舱_行业指标
  enterprise: 'dstREPLACE_ENTERPRISE',  // 电力驾驶舱_重点企业
  loadCurve: 'dstREPLACE_LOADCURVE',    // 电力驾驶舱_用电曲线
  alert: 'dstREPLACE_ALERT',            // 电力驾驶舱_预警事件
  renewable: 'dstREPLACE_RENEWABLE',    // 电力驾驶舱_新能源充电
  insight: 'dstREPLACE_INSIGHT',        // 电力驾驶舱_机器人洞察
  config: 'dstREPLACE_CONFIG',          // 电力驾驶舱_配置参数
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
