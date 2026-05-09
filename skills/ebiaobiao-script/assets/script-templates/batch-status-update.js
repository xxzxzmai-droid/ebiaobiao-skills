const datasheet = await space.getActiveDatasheetAsync();
const statusField = await input.fieldAsync('选择状态字段', datasheet);
const newStatus = await input.textAsync('输入要写入的新状态');
const records = await input.recordsAsync('选择要更新的记录', datasheet);

if (!records.length) {
  output.markdown('未选择记录。');
} else {
  const confirmed = await input.buttonsAsync(`确认更新 ${records.length} 条记录？`, [
    { label: '确认更新', value: true },
    { label: '取消', value: false },
  ]);
  if (confirmed) {
    const updates = records.map((record) => ({
      recordId: record.id,
      fields: { [statusField.id]: newStatus },
    }));
    await datasheet.updateRecordsAsync(updates);
    output.markdown(`已更新 ${records.length} 条记录。`);
  }
}
