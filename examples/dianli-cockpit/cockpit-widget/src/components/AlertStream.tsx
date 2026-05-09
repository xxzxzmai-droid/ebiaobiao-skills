import React, { useMemo } from 'react';
import { theme, colorOf, ALERT_LEVEL_COLOR, ALERT_STATUS_COLOR } from '../theme';
import { Pill } from './primitives/Pill';
import { PulseDot } from './primitives/PulseDot';
import { relativeTime } from '../utils/format';

interface AlertStreamProps {
  data: Array<Record<string, unknown>>;
  selectedDistrict?: string | null;
  limit?: number;
  /** 点击预警条目时回调（传 recordId） */
  onSelectAlert?: (recordId: string) => void;
}

/** 实时预警事件流。红色 entry 脉动闪烁。点击打开状态切换抽屉。 */
export const AlertStream: React.FC<AlertStreamProps> = ({
  data, selectedDistrict, limit = 30, onSelectAlert,
}) => {
  const filtered = useMemo(() => {
    let arr = data;
    if (selectedDistrict) arr = arr.filter((r) => r['区域'] === selectedDistrict);
    // 按时间倒序
    return [...arr].sort((a, b) => {
      const ta = new Date(String(a['时间'] || '')).getTime();
      const tb = new Date(String(b['时间'] || '')).getTime();
      return tb - ta;
    }).slice(0, limit);
  }, [data, selectedDistrict, limit]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        fontSize: 12, color: theme.textSecondary, marginBottom: 8,
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <PulseDot color={theme.danger} size={6} />
        实时预警 {selectedDistrict ? `· ${selectedDistrict}` : ''}
        <span style={{ color: theme.textTertiary, marginLeft: 'auto' }}>
          {filtered.length} / {data.length}
        </span>
      </div>
      <div style={{
        flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6,
        paddingRight: 4,
      }}>
        {filtered.length === 0 && (
          <div style={{ color: theme.textTertiary, fontSize: 12, textAlign: 'center', padding: 24 }}>
            当前无预警
          </div>
        )}
        {filtered.map((r, i) => {
          const level = String(r['等级'] || '黄色');
          const isRed = level === '红色';
          const code = String(r['标题'] || '').slice(0, 12);    // AL-XXXX
          const recId = String(r['__id'] || '');
          return (
            <div key={recId || i}
                 onClick={onSelectAlert && recId ? () => onSelectAlert(recId) : undefined}
                 style={{
                   padding: '8px 10px',
                   borderRadius: 6,
                   border: `1px solid ${colorOf(ALERT_LEVEL_COLOR[level])}55`,
                   background: `${colorOf(ALERT_LEVEL_COLOR[level])}0d`,
                   display: 'flex', flexDirection: 'column', gap: 4,
                   animation: isRed ? 'redPulse 2s ease-in-out infinite' : undefined,
                   cursor: onSelectAlert ? 'pointer' : 'default',
                   transition: 'transform 0.15s ease, border-color 0.15s ease',
                 }}
                 onMouseEnter={onSelectAlert ? (e) => {
                   (e.currentTarget as HTMLDivElement).style.borderColor = colorOf(ALERT_LEVEL_COLOR[level]);
                   (e.currentTarget as HTMLDivElement).style.transform = 'translateX(-2px)';
                 } : undefined}
                 onMouseLeave={onSelectAlert ? (e) => {
                   (e.currentTarget as HTMLDivElement).style.borderColor = `${colorOf(ALERT_LEVEL_COLOR[level])}55`;
                   (e.currentTarget as HTMLDivElement).style.transform = 'none';
                 } : undefined}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Pill label={level} color={ALERT_LEVEL_COLOR[level]} size="sm" />
                <span style={{ fontSize: 11, color: theme.textSecondary,
                               fontFamily: 'monospace' }}>{code}</span>
                <Pill label={String(r['类型'] || '')} color="gray" size="sm" />
                <span style={{ marginLeft: 'auto', fontSize: 10, color: theme.textTertiary }}>
                  {relativeTime(String(r['时间'] || ''))}
                </span>
              </div>
              <div style={{ fontSize: 12, color: theme.textPrimary, lineHeight: 1.4,
                            display: '-webkit-box', WebkitBoxOrient: 'vertical',
                            WebkitLineClamp: 2, overflow: 'hidden' }}>
                {String(r['说明'] || '').replace(/^【[^】]+】/, '')}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 10, color: theme.textTertiary }}>{String(r['区域'] || '')}</span>
                <span style={{ flex: 1 }} />
                <Pill label={String(r['状态'] || '')}
                      color={ALERT_STATUS_COLOR[String(r['状态'] || '')]}
                      size="sm" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
