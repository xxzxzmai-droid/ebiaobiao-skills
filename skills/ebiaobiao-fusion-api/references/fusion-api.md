# Fusion API Reference

## Official Boundaries

- Public base URL in official docs: `https://vika.cn/fusion/v1/`.
- Private e报表 base URL: `https://app.ehv.csg.cn:7886/fusion/v1/`.
- HTTPS is required.
- Auth header: `Authorization: Bearer {API Token}`.
- API permissions equal the token owner's UI permissions.
- Common IDs: `spc` space, `dst` datasheet, `viw` view, `fld` field, `rec` record, `fod` folder, `fom` form, `dsb` dashboard.

## Endpoints

- `GET /spaces`: list spaces.
- `GET /spaces/{spaceId}/nodes`: list file nodes/directories.
- `GET /fusion/v2/spaces/{spaceId}/nodes?type=Datasheet`: search nodes. Use the v2 base for this endpoint.
- `GET /spaces/{spaceId}/nodes/{nodeId}`: node details.
- `POST /spaces/{spaceId}/datasheets`: create datasheet.
- `GET /datasheets/{datasheetId}/fields`: list fields.
- `POST /spaces/{spaceId}/datasheets/{datasheetId}/fields`: create field.
- `DELETE /spaces/{spaceId}/datasheets/{datasheetId}/fields/{fieldId}`: delete field.
- `GET /datasheets/{datasheetId}/views`: list views.
- `GET /datasheets/{datasheetId}/records`: query records.
- `POST /datasheets/{datasheetId}/records`: create records.
- `PATCH /datasheets/{datasheetId}/records`: update records.
- `DELETE /datasheets/{datasheetId}/records?recordIds=...`: delete records.
- `POST /datasheets/{datasheetId}/attachments`: upload one attachment.

## Payload Reminders

Create datasheet:

```json
{
  "name": "表格标题",
  "description": "表格描述",
  "folderId": "optional-fod-id",
  "fields": [
    { "type": "SingleText", "name": "标题", "property": { "defaultValue": "" } }
  ]
}
```

Create field:

```json
{ "type": "SingleText", "name": "新增文本字段", "property": { "defaultValue": "" } }
```

Checkbox fields require an icon:

```json
{ "type": "Checkbox", "name": "确认", "property": { "icon": "white_check_mark" } }
```

MultiSelect fields can be created with option names:

```json
{
  "type": "MultiSelect",
  "name": "彩虹标签",
  "property": {
    "options": [
      { "name": "红-领导交办" },
      { "name": "橙-跨部门协同" }
    ]
  }
}
```

Create records:

```json
[
  { "fields": { "字段名称": "value" } }
]
```

Update records:

```json
[
  { "recordId": "recxxxx", "fields": { "字段名称": "value" } }
]
```

## Safety Rules

- Discover fields and views first; store field IDs for durable reads and mapping.
- Use field names for create/update record `fields` maps unless the live API version is verified to support field IDs.
- Live smoke on private e报表 confirmed that creating records with field IDs returns `400 The format of the fields parameter value is wrong`; retry with field names before debugging token or permissions.
- Live matrix on the private e报表 host confirmed node search uses the v2 base and field deletion needs the `spaces/{spaceId}` path segment.
- Checkbox field creation fails with `"icon" is required` unless `property.icon` is supplied.
- Live work-supervision smoke confirmed MultiSelect record writes accept arrays of option names when using field-name payloads; `cellFormat=string` reads them back as comma-separated text.
- Checkbox field `property.icon` may be normalized by the server from `white_check_mark` to `✅`; checkbox records may read `true` as `"1"` and false as `"0"` or absent depending on endpoint/format. Treat absent/`0`/false as unchecked.
- New datasheets can contain default blank rows. Clean them before seeding records, otherwise useful data appears after the blank rows in the UI.
- Avoid writing computed fields: formula, lookup, auto number, created/modified metadata.
- Use `unitId` for member fields.
- Treat attachments as two-step: upload, then write returned attachment object into an attachment field.
- The API can return HTTP 200 with `success=false`; always check both HTTP status and business status.
- Back off on `429`; the bundled CLI retries transient failures.
