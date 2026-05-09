const datasheet = await space.getActiveDatasheetAsync();
const fields = await datasheet.getFieldsAsync();
const requiredFields = await input.fieldsAsync('选择需要校验必填的字段', datasheet);
const records = await datasheet.getRecordsAsync();

const problems = [];
for (const record of records) {
  const missing = [];
  for (const field of requiredFields) {
    const value = record.getCellValue(field.id);
    const emptyArray = Array.isArray(value) && value.length === 0;
    if (value === null || value === undefined || value === '' || emptyArray) {
      missing.push(field.name);
    }
  }
  if (missing.length) {
    problems.push({
      recordId: record.id,
      title: record.title,
      missing: missing.join('、'),
    });
  }
}

output.markdown(`共检查 ${records.length} 条记录，发现 ${problems.length} 条缺失。`);
if (problems.length) {
  output.table(problems);
}
