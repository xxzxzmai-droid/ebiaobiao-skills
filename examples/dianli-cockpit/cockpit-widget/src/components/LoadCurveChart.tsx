import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { theme, colorOf, DISTRICT_COLOR } from '../theme';
import { formatTime } from '../utils/format';

interface LoadCurveChartProps {
  data: Array<Record<string, unknown>>;   // load_curve 表的归一化记录
  selectedDistrict?: string | null;
}

/**
 * 24 小时用电曲线（按区域分系列），ECharts 折线图，深色 + 渐变发光。
 *
 * 把 data 按区域 group → 7 条线。selectedDistrict 时只画那一条。
 */
export const LoadCurveChart: React.FC<LoadCurveChartProps> = ({ data, selectedDistrict }) => {
  const ref = useRef<HTMLDivElement>(null);
  const instRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const inst = echarts.init(ref.current, undefined, { renderer: 'svg' });
    instRef.current = inst;
    const onResize = () => inst.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      inst.dispose();
      instRef.current = null;
    };
  }, []);

  useEffect(() => {
    const inst = instRef.current;
    if (!inst) return;

    // 按 区域 group
    const byDistrict = new Map<string, Array<[string, number]>>();
    for (const r of data) {
      const ts = r['时间戳'] as string;
      const district = r['区域'] as string;
      const load = Number(r['实时负荷_MW']);
      if (!ts || !district || isNaN(load)) continue;
      if (selectedDistrict && district !== selectedDistrict) continue;
      const arr = byDistrict.get(district) || [];
      arr.push([ts, load]);
      byDistrict.set(district, arr);
    }
    // sort by time
    for (const arr of byDistrict.values()) arr.sort((a, b) => a[0].localeCompare(b[0]));

    const series: echarts.LineSeriesOption[] = Array.from(byDistrict.entries()).map(
      ([district, points]) => ({
        name: district,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        showSymbol: false,
        data: points.map(([t, v]) => [formatTime(t), v]),
        lineStyle: {
          width: selectedDistrict ? 2.5 : 1.5,
          color: colorOf(DISTRICT_COLOR[district]),
          shadowColor: colorOf(DISTRICT_COLOR[district]),
          shadowBlur: 8,
        },
        areaStyle: selectedDistrict ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `${colorOf(DISTRICT_COLOR[district])}55` },
            { offset: 1, color: `${colorOf(DISTRICT_COLOR[district])}05` },
          ]),
        } : undefined,
        emphasis: { focus: 'series' },
      }),
    );

    inst.setOption({
      backgroundColor: 'transparent',
      grid: { left: 40, right: 16, top: 28, bottom: 30 },
      legend: {
        textStyle: { color: theme.textSecondary, fontSize: 10 },
        top: 0,
        right: 8,
        itemWidth: 10,
        itemHeight: 6,
        type: 'scroll',
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 31, 53, 0.95)',
        borderColor: theme.border,
        textStyle: { color: theme.textPrimary, fontSize: 11 },
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        axisLine: { lineStyle: { color: theme.borderStrong } },
        axisLabel: { color: theme.textSecondary, fontSize: 10 },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        name: 'MW',
        nameTextStyle: { color: theme.textTertiary, fontSize: 10 },
        axisLine: { show: false },
        axisLabel: { color: theme.textSecondary, fontSize: 10 },
        splitLine: { lineStyle: { color: theme.border, type: 'dashed' } },
      },
      series,
    }, { notMerge: true });
  }, [data, selectedDistrict]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ fontSize: 12, color: theme.textSecondary, marginBottom: 6 }}>
        24 小时用电曲线 {selectedDistrict ? `· ${selectedDistrict}` : '· 全市'}
      </div>
      <div ref={ref} style={{ flex: 1, minHeight: 180, width: '100%' }} />
    </div>
  );
};
