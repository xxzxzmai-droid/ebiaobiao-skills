import React, { useMemo, useState } from 'react';
import {
  FieldPicker,
  ViewPicker,
  useActiveViewId,
  useCloudStorage,
  useDatasheet,
  useFields,
  useRecords,
} from '@apitable/widget-sdk';
import styles from './style.css';

type FieldMap = {
  amountFieldId?: string;
  statusFieldId?: string;
};

export function App() {
  const datasheet = useDatasheet();
  const activeViewId = useActiveViewId();
  const [viewId, setViewId] = useCloudStorage<string | undefined>('ebiao:viewId', activeViewId);
  const [fieldMap, setFieldMap] = useCloudStorage<FieldMap>('ebiao:fieldMap', {});
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState('');
  const fields = useFields(viewId);
  const records = useRecords(viewId);

  const summary = useMemo(() => {
    let total = 0;
    let valid = 0;
    for (const record of records ?? []) {
      const value = fieldMap.amountFieldId ? record.getCellValue(fieldMap.amountFieldId) : null;
      if (typeof value === 'number') {
        total += value;
        valid += 1;
      }
    }
    const count = records?.length ?? 0;
    const completion = count ? Math.round((valid / count) * 100) : 0;
    return { total, valid, count, completion };
  }, [records, fieldMap.amountFieldId]);

  async function markChecked() {
    if (!datasheet || !fieldMap.statusFieldId || !records?.length) return;
    const values = records.slice(0, 10).map((record) => ({
      id: record.id,
      valuesMap: { [fieldMap.statusFieldId!]: '已校验' },
    }));
    const check = datasheet.checkPermissionsForSetRecords(values);
    if (!check.acceptable) {
      setMessage(check.message || '当前用户无批量更新权限');
      return;
    }
    setRunning(true);
    setMessage('');
    try {
      await datasheet.setRecords(values);
      setMessage(`已回写 ${values.length} 条记录`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '回写失败');
    } finally {
      setRunning(false);
    }
  }

  if (!datasheet || !fields) {
    return <main className={styles.app}><div className={styles.state}>加载中...</div></main>;
  }

  return (
    <main className={styles.app}>
      <section className={styles.topbar}>
        <div>
          <span className={styles.eyebrow}>e报表业务助手</span>
          <h1>e报表业务助手</h1>
          <p>选择视图和字段后预览校验结果，再执行批量处理。</p>
          <div className={styles.badges}>
            <span>权限检查</span>
            <span>多端自适应</span>
            <span>Token 不进前端</span>
          </div>
        </div>
        <button className={styles.primary} disabled={running || !fieldMap.statusFieldId || !summary.count} onClick={markChecked}>
          {running ? '处理中' : '回写状态'}
        </button>
      </section>

      <section className={styles.controls} aria-label="字段配置">
        <label>
          <span>视图</span>
          <ViewPicker viewId={viewId} onChange={(option) => setViewId(option.value)} />
        </label>
        <label>
          <span>金额字段</span>
          <FieldPicker datasheet={datasheet} viewId={viewId} fieldId={fieldMap.amountFieldId} onChange={(option) => setFieldMap({ ...fieldMap, amountFieldId: option.value })} />
        </label>
        <label>
          <span>状态字段</span>
          <FieldPicker datasheet={datasheet} viewId={viewId} fieldId={fieldMap.statusFieldId} onChange={(option) => setFieldMap({ ...fieldMap, statusFieldId: option.value })} />
        </label>
      </section>

      <section className={styles.summary} aria-label="汇总">
        <div><span>记录数</span><strong>{summary.count}</strong></div>
        <div><span>有效金额行</span><strong>{summary.valid}</strong></div>
        <div><span>完成率</span><strong>{summary.completion}%</strong><i style={{ width: `${summary.completion}%` }} /></div>
        <div><span>金额合计</span><strong>{summary.total.toLocaleString('zh-CN')}</strong></div>
      </section>

      {message ? <section className={styles.message}>{message}</section> : null}
    </main>
  );
}
