const datasheet = await space.getActiveDatasheetAsync();
const field = await input.fieldAsync('选择要查找替换的文本字段', datasheet);
const findText = await input.textAsync('请输入要查找的文本');
const replaceText = await input.textAsync('请输入替换后的文本');
const dryRun = await input.buttonsAsync('是否先预览？', [
  { label: '先预览', value: true },
  { label: '直接替换', value: false },
]);

const records = await datasheet.getRecordsAsync();
const updates = [];
for (const record of records) {
  const value = record.getCellValueString(field.id);
  if (value && value.includes(findText)) {
    updates.push({
      recordId: record.id,
      fields: {
        [field.id]: value.split(findText).join(replaceText),
      },
    });
  }
}

output.markdown(`匹配 ${updates.length} 条记录。`);
if (dryRun || !updates.length) {
  output.table(updates.map((item) => ({ recordId: item.recordId, newValue: item.fields[field.id] })));
} else {
  await datasheet.updateRecordsAsync(updates);
  output.markdown(`已替换 ${updates.length} 条记录。`);
}
