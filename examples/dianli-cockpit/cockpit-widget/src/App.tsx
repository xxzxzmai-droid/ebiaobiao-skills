import React, { useMemo, useState } from 'react';
import { useResponsive } from './hooks/useResponsive';
import { useDistrictFilter } from './hooks/useDistrictFilter';
import { useCockpitData } from './hooks/useCockpitData';
import { useConfigKV } from './hooks/useConfigKV';

import { theme } from './theme';
import { HeaderBar } from './components/HeaderBar';
import { KpiRow } from './components/KpiRow';
import { HuizhouMap } from './components/HuizhouMap';
import { LoadCurveChart } from './components/LoadCurveChart';
import { IndustryDonut } from './components/IndustryDonut';
import { AlertStream } from './components/AlertStream';
import { EnterpriseTop10 } from './components/EnterpriseTop10';
import { InsightTicker } from './components/InsightTicker';
import { AlertStatusEditor } from './components/AlertStatusEditor';

export function App() {
  const { isMobile, isBigScreen } = useResponsive();
  const filter = useDistrictFilter();
  const { ready, industry, enterprise, loadCurve, alert, insight, config, datasheets } = useCockpitData();
  const configKV = useConfigKV(config);

  // 乐观更新：alert 状态本地覆盖（recordId → newStatus）
  const [statusOverrides, setStatusOverrides] = useState<Record<string, string>>({});
  const [editingAlertId, setEditingAlertId] = useState<string | null>(null);

  // alert 数据应用本地 overrides（视觉先变）
  const alertWithOverrides = useMemo(() => {
    if (!Object.keys(statusOverrides).length) return alert;
    return alert.map((r) => {
      const id = String(r['__id'] || '');
      const override = statusOverrides[id];
      return override ? { ...r, '状态': override } : r;
    });
  }, [alert, statusOverrides]);

  const editingAlert = editingAlertId
    ? alert.find((r) => String(r['__id']) === editingAlertId)
    : null;

  // 区域用电热力（归一化）
  const districtIntensity = useMemo(() => {
    const m: Record<string, number> = {};
    for (const r of loadCurve) {
      const d = String(r['区域'] || '');
      const v = Number(r['累计用电_MWh'] || 0);
      m[d] = (m[d] || 0) + v;
    }
    const max = Math.max(1, ...Object.values(m));
    return Object.fromEntries(Object.entries(m).map(([k, v]) => [k, v / max]));
  }, [loadCurve]);

  if (!ready) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', color: theme.textSecondary,
                    background: theme.bg, fontSize: 14 }}>
        正在连接数据表...
      </div>
    );
  }

  // 三档布局
  const Layout = isMobile ? MobileLayout : isBigScreen ? BigScreenLayout : CompactLayout;

  return (
    <div style={{ height: '100vh', background: theme.bg, color: theme.textPrimary,
                  display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <HeaderBar
        filterDistrict={filter.district}
        filterIndustry={filter.industry}
        onResetFilter={filter.reset}
      />
      <KpiRow
        loadCurve={loadCurve}
        industry={industry}
        alerts={alertWithOverrides}
        enterprises={enterprise}
        configKV={configKV}
      />
      <Layout
        industry={industry}
        loadCurve={loadCurve}
        enterprises={enterprise}
        alerts={alertWithOverrides}
        districtIntensity={districtIntensity}
        filter={filter}
        onSelectAlert={setEditingAlertId}
      />
      <InsightTicker data={insight} />

      {editingAlert && (
        <AlertStatusEditor
          datasheet={datasheets.alert}
          recordId={editingAlertId!}
          currentStatus={String(editingAlert['状态'] || '处理中')}
          onClose={() => setEditingAlertId(null)}
          onLocalUpdate={(newStatus) => {
            setStatusOverrides((prev) => ({ ...prev, [editingAlertId!]: newStatus }));
          }}
          onRollback={(original) => {
            setStatusOverrides((prev) => {
              const { [editingAlertId!]: _, ...rest } = prev;
              return rest;
            });
          }}
        />
      )}
    </div>
  );
}

interface LayoutProps {
  industry: Array<Record<string, unknown>>;
  loadCurve: Array<Record<string, unknown>>;
  enterprises: Array<Record<string, unknown>>;
  alerts: Array<Record<string, unknown>>;
  districtIntensity: Record<string, number>;
  filter: ReturnType<typeof useDistrictFilter>;
  onSelectAlert?: (recordId: string) => void;
}

const BigScreenLayout: React.FC<LayoutProps> = ({
  industry, loadCurve, enterprises, alerts, districtIntensity, filter, onSelectAlert,
}) => (
  <div style={{ flex: 1, padding: '0 16px 12px', display: 'grid',
                gridTemplateRows: '1fr 1fr', gap: 12, overflow: 'hidden' }}>
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr 1fr',
                  gap: 12, minHeight: 0 }}>
      <Panel><HuizhouMap intensity={districtIntensity}
                         selected={filter.district}
                         onSelect={filter.setDistrict} /></Panel>
      <Panel><LoadCurveChart data={loadCurve}
                              selectedDistrict={filter.district} /></Panel>
      <Panel><AlertStream data={alerts} selectedDistrict={filter.district} onSelectAlert={onSelectAlert} /></Panel>
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr',
                  gap: 12, minHeight: 0 }}>
      <Panel><IndustryDonut data={industry}
                             selectedIndustry={filter.industry}
                             onSelect={filter.setIndustry} /></Panel>
      <Panel><EnterpriseTop10 data={enterprises}
                              selectedDistrict={filter.district}
                              selectedIndustry={filter.industry} /></Panel>
    </div>
  </div>
);

const CompactLayout: React.FC<LayoutProps> = ({
  industry, loadCurve, enterprises, alerts, districtIntensity, filter, onSelectAlert,
}) => (
  <div style={{ flex: 1, padding: '0 12px 12px', display: 'grid',
                gridTemplateColumns: '1fr 1fr', gridTemplateRows: 'auto 1fr 1fr',
                gap: 10, overflow: 'auto' }}>
    <Panel style={{ gridColumn: '1 / 3', height: 240 }}>
      <HuizhouMap intensity={districtIntensity}
                  selected={filter.district}
                  onSelect={filter.setDistrict} />
    </Panel>
    <Panel><LoadCurveChart data={loadCurve}
                            selectedDistrict={filter.district} /></Panel>
    <Panel><AlertStream data={alerts} selectedDistrict={filter.district} /></Panel>
    <Panel><IndustryDonut data={industry}
                           selectedIndustry={filter.industry}
                           onSelect={filter.setIndustry} /></Panel>
    <Panel><EnterpriseTop10 data={enterprises}
                            selectedDistrict={filter.district}
                            selectedIndustry={filter.industry} /></Panel>
  </div>
);

const MobileLayout: React.FC<LayoutProps> = ({
  industry, loadCurve, enterprises, alerts, districtIntensity, filter, onSelectAlert,
}) => (
  <div style={{ flex: 1, padding: '0 12px 12px', display: 'flex',
                flexDirection: 'column', gap: 10, overflow: 'auto' }}>
    <Panel style={{ minHeight: 200 }}>
      <HuizhouMap intensity={districtIntensity}
                  selected={filter.district}
                  onSelect={filter.setDistrict} />
    </Panel>
    <Panel style={{ minHeight: 220 }}>
      <LoadCurveChart data={loadCurve} selectedDistrict={filter.district} />
    </Panel>
    <Panel style={{ minHeight: 240 }}>
      <IndustryDonut data={industry}
                     selectedIndustry={filter.industry}
                     onSelect={filter.setIndustry} />
    </Panel>
    <Panel style={{ minHeight: 280 }}>
      <AlertStream data={alerts} selectedDistrict={filter.district} />
    </Panel>
    <Panel style={{ minHeight: 280 }}>
      <EnterpriseTop10 data={enterprises}
                       selectedDistrict={filter.district}
                       selectedIndustry={filter.industry} />
    </Panel>
  </div>
);

const Panel: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> =
  ({ children, style }) => (
  <div style={{
    background: theme.gradientPanel,
    border: `1px solid ${theme.border}`,
    borderRadius: 8,
    padding: 12,
    overflow: 'hidden',
    minWidth: 0,
    minHeight: 0,
    ...style,
  }}>
    {children}
  </div>
);
