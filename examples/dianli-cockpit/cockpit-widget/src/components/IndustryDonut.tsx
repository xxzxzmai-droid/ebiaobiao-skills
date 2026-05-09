import React, { useEffect, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { theme, colorOf, INDUSTRY_COLOR } from '../theme';

interface IndustryDonutProps {
  data: Array<Record<string, unknown>>;          // industry 表
  selectedIndustry?: string | null;
  onSelect?: (industry: string | null) => void;
}

/** 6 行业用电构成 donut。点击块切过滤。 */
export const IndustryDonut: React.FC<IndustryDonutProps> = ({
  data, selectedIndustry, onSelect,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const instRef = useRef<echarts.ECharts | null>(null);

  // 按行业聚合用电
  const aggregated = useMemo(() => {
    const m = new Map<string, number>();
    for (const r of data) {
      const ind = r['行业'] as string;
      const power = Number(r['行业用电_MWh']);
      if (!ind || isNaN(power)) continue;
      m.set(ind, (m.get(ind) || 0) + power);
    }
    return Array.from(m.entries()).map(([name, value]) => ({ name, value }));
  }, [data]);

  useEffect(() => {
    if (!ref.current) return;
    const inst = echarts.init(ref.current, undefined, { renderer: 'svg' });
    instRef.current = inst;
    inst.on('click', (params: any) => {
      if (params?.name && onSelect) {
        onSelect(params.name === selectedIndustry ? null : params.name);
      }
    });
    const onResize = () => inst.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      inst.dispose();
      instRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const inst = instRef.current;
    if (!inst) return;
    inst.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 31, 53, 0.95)',
        borderColor: theme.border,
        textStyle: { color: theme.textPrimary, fontSize: 11 },
        valueFormatter: (v: number) => `${(v / 10000).toFixed(2)} 万 MWh`,
      },
      legend: {
        type: 'scroll',
        bottom: 0,
        textStyle: { color: theme.textSecondary, fontSize: 10 },
        itemWidth: 10, itemHeight: 6,
      },
      series: [{
        type: 'pie',
        radius: ['52%', '76%'],
        center: ['50%', '46%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: theme.bg,
          borderWidth: 2,
          shadowBlur: 8,
        },
        label: {
          show: true,
          color: theme.textSecondary,
          fontSize: 10,
          formatter: '{b}',
        },
        labelLine: { lineStyle: { color: theme.border } },
        emphasis: {
          itemStyle: { shadowBlur: 16 },
          label: { color: theme.primary, fontWeight: 700 },
        },
        data: aggregated.map((item) => ({
          ...item,
          itemStyle: {
            color: colorOf(INDUSTRY_COLOR[item.name]),
            opacity: !selectedIndustry || selectedIndustry === item.name ? 1 : 0.3,
          },
        })),
      }],
    }, { notMerge: true });
  }, [aggregated, selectedIndustry]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ fontSize: 12, color: theme.textSecondary, marginBottom: 6 }}>
        行业用电构成 {selectedIndustry ? `· ${selectedIndustry}` : '· 全部'}
      </div>
      <div ref={ref} style={{ flex: 1, minHeight: 200, width: '100%' }} />
    </div>
  );
};
