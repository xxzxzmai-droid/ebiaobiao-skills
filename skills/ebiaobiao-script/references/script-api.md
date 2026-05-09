# Script API Reference

## Main APIs

- `space`: access current space and datasheets.
- `space.getActiveDatasheetAsync()`: get active datasheet.
- `datasheet.getFieldsAsync()`, `datasheet.getRecordsAsync()`, `datasheet.getRecordAsync()`: inspect data.
- `datasheet.setRecordsAsync()` or equivalent batch update APIs: update records when supported by the runtime version.
- `input`: prompt users for text, fields, records, select choices, confirmation, and files where supported.
- `output`: print text, tables, markdown, and result summaries.
- `fetch`: call external APIs.
- `_`: lodash helper.

## Script Shape

```javascript
const datasheet = await space.getActiveDatasheetAsync();
const field = await input.fieldAsync('选择字段', datasheet);
const records = await datasheet.getRecordsAsync();
output.markdown(`读取 ${records.length} 条记录`);
```

## Safety

- Show affected row counts before writing.
- Skip computed fields and unsupported fields.
- Keep a `dryRun` or confirmation step for destructive changes.
- Avoid exposing tokens in source. Use backend endpoints for privileged external calls.
- Print row-level errors as a table with record title/ID and reason.
