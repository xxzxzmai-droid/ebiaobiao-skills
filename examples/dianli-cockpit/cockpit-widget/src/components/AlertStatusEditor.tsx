import React, { useEffect, useState } from 'react';
import { useFields } from '@apitable/widget-sdk';
import { theme, ALERT_STATUS_COLOR, colorOf } from '../theme';
import { Pill } from './primitives/Pill';

interface Props {
  /** widget-sdk Datasheet 对象（alert 表） */
  datasheet: any;
  recordId: string;
  currentStatus: string;
  /** 关闭抽屉 */
  onClose: () => void;
  /** 乐观更新成功后调用 */
  onLocalUpdate: (newStatus: string) => void;
  /** 失败时调用，让上层回滚 */
  onRollback: (originalStatus: string) => void;
}

const STATUSES = ['处理中', '已纳入监测', '已闭环', '已忽略'] as const;

/**
 * 预警状态切换抽屉。
 *
 * 乐观更新：立即调上层 onLocalUpdate（视觉先变），然后异步 setRecords。
 * 失败：调 onRollback 还原 + toast 错误。权限不够：禁用按钮 + 提示。
 */
export const AlertStatusEditor: React.FC<Props> = ({
  datasheet, recordId, currentStatus, onClose, onLocalUpdate, onRollback,
}) => {
  const fields = useFields(datasheet) as any[];
  const statusField = fields?.find((f) => f.name === '状态');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [permError, setPermError] = useState<string | null>(null);

  // 进场动画
  const [visible, setVisible] = useState(false);
  useEffect(() => { setVisible(true); }, []);

  async function handleSelect(newStatus: string) {
    if (newStatus === currentStatus) return;
    if (!statusField) {
      setError('未找到"状态"字段');
      return;
    }
    if (busy) return;

    const original = currentStatus;
    setBusy(true);
    setError(null);

    // 1. 权限检查
    try {
      const check = datasheet.checkPermissionsForSetRecords?.([{
        id: recordId,
        valuesMap: { [statusField.id]: newStatus },
      }]);
      if (check && !check.acceptable) {
        setPermError(check.message || '当前用户无写入权限');
        setBusy(false);
        return;
      }
    } catch {
      // 老版本 sdk 没这个 api，直接试写
    }

    // 2. 乐观更新（视觉立即变）
    onLocalUpdate(newStatus);

    // 3. 异步写回
    try {
      await datasheet.setRecords([{
        id: recordId,
        valuesMap: { [statusField.id]: newStatus },
      }]);
      // 成功：关抽屉
      setBusy(false);
      handleClose();
    } catch (err: any) {
      // 失败：回滚 + toast
      onRollback(original);
      setError(err?.message || '写回失败，已回滚');
      setBusy(false);
    }
  }

  function handleClose() {
    setVisible(false);
    setTimeout(onClose, 200);
  }

  return (
    <>
      {/* 遮罩 */}
      <div
        onClick={handleClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(10, 25, 41, 0.7)',
          backdropFilter: 'blur(2px)',
          opacity: visible ? 1 : 0,
          transition: 'opacity 0.2s ease',
        }}
      />
      {/* 抽屉 */}
      <div style={{
        position: 'fixed', right: 0, top: 0, bottom: 0, width: 360,
        maxWidth: '100vw', zIndex: 101,
        background: theme.bgPanelSolid,
        borderLeft: `1px solid ${theme.borderStrong}`,
        boxShadow: '-8px 0 32px rgba(0, 217, 255, 0.15)',
        padding: 20, display: 'flex', flexDirection: 'column', gap: 16,
        transform: visible ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.25s ease',
        color: theme.textPrimary,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700,
                       color: theme.primary, textShadow: theme.glowText(theme.primary) }}>
            预警状态切换
          </h2>
          <span style={{ flex: 1 }} />
          <button onClick={handleClose}
                  style={{ background: 'transparent', border: 'none',
                           color: theme.textSecondary, fontSize: 18,
                           cursor: 'pointer', padding: 4 }}>
            ✕
          </button>
        </div>

        <div style={{ fontSize: 11, color: theme.textTertiary }}>
          recordId: <code style={{ color: theme.textSecondary }}>{recordId.slice(-12)}</code>
        </div>

        <div>
          <div style={{ fontSize: 11, color: theme.textSecondary, marginBottom: 6 }}>
            当前状态
          </div>
          <Pill label={currentStatus}
                color={ALERT_STATUS_COLOR[currentStatus]} size="md" />
        </div>

        <div style={{ borderTop: `1px solid ${theme.border}`, paddingTop: 12 }}>
          <div style={{ fontSize: 11, color: theme.textSecondary, marginBottom: 8 }}>
            切换为
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {STATUSES.map((s) => {
              const isCurrent = s === currentStatus;
              const fg = colorOf(ALERT_STATUS_COLOR[s]);
              return (
                <button
                  key={s}
                  disabled={busy || isCurrent || !!permError}
                  onClick={() => handleSelect(s)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    background: isCurrent ? `${fg}33` : `${fg}11`,
                    border: `1px solid ${isCurrent ? fg : `${fg}55`}`,
                    color: isCurrent ? fg : theme.textPrimary,
                    padding: '10px 14px',
                    borderRadius: 6,
                    cursor: (busy || isCurrent || permError) ? 'default' : 'pointer',
                    fontSize: 13,
                    fontWeight: 600,
                    textAlign: 'left',
                    opacity: (busy || permError) ? 0.5 : 1,
                    transition: 'all 0.15s ease',
                    minHeight: 44,
                  }}>
                  <Pill label={s} color={ALERT_STATUS_COLOR[s]} size="sm" />
                  {isCurrent && (
                    <span style={{ marginLeft: 'auto', fontSize: 11,
                                   color: theme.textTertiary }}>
                      当前
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {permError && (
          <div style={{
            background: `${theme.warning}22`,
            border: `1px solid ${theme.warning}55`,
            padding: '10px 12px', borderRadius: 6,
            color: theme.warning, fontSize: 12, lineHeight: 1.5,
          }}>
            ⚠ {permError}
          </div>
        )}
        {error && (
          <div style={{
            background: `${theme.danger}22`,
            border: `1px solid ${theme.danger}55`,
            padding: '10px 12px', borderRadius: 6,
            color: theme.danger, fontSize: 12, lineHeight: 1.5,
          }}>
            ✗ {error}
          </div>
        )}
        {busy && (
          <div style={{ color: theme.textSecondary, fontSize: 11, textAlign: 'center' }}>
            写入中...
          </div>
        )}
      </div>
    </>
  );
};
