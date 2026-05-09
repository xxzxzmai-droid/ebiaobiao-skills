# Fusion API 实战踩坑（私有部署 vika）

`examples/dianli-cockpit/` Phase A 真灌入 ~1300 条种子数据踩到的坑。后来者按这里避开。

## 1. 主字段名固定为 `标题`，不能改

新建 datasheet 时 vika 自动创建 3 个字段：

| 字段 | 类型 | 备注 |
|---|---|---|
| 标题 | SingleText | **primary**，不可改名（API 没提供 rename-field） |
| 选项 | MultiSelect | 空 options，可删 |
| 附件 | Attachment | 可删 |

把概念主键（如 "企业名称"、"事件编号"、"参数"）放到这里：

```python
# 错（API 报 "Invalid fields"）
records = [{"参数": "红色阈值", "值": "80"}, ...]

# 对：使用 标题 作为概念主键的实际存储
records = [{"标题": "红色阈值", "值": "80"}, ...]
```

UI 列名仍叫"标题"，可在 UI 手动重命名为概念名，**不影响数据**。

## 2. 创建 datasheet 时复杂字段必须发完整 property

Schema 校验严格——SingleSelect / Rating / Number / DateTime / CreatedTime / LastModifiedTime 创建时必须提供完整 property。**省略**会报：

```
Invalid value for fields[X].property
```

错误信息有误导性（看起来像"property 值错"），实际是"property 缺失"。

**推荐工作流**：
1. `create-datasheet` 只带 name 建空表
2. 用 `create-field` 一个个补复杂字段（每次单独 payload）

不要一次性 create-datasheet 时把所有 fields 塞进去，除非你 100% 确定每个 property 完整。

## 3. 单批写记录 ≤ 10 条（CLI 自动分批）

REST API 硬上限。`ebiao_fusion.py create-records` 自动分批 + 支持 `--sleep` 控速。**调用方传整批让 CLI 处理**，不要在客户端再分一次：

```python
# 错（每批 10 条独立 subprocess，开销大、易超时）
for chunk in chunks(records, 10):
    subprocess.run([..., 'create-records', dst, json.dumps([{"fields":r} for r in chunk])])

# 对（一次性给 CLI，让它内部分块）
subprocess.run([..., 'create-records', dst,
                json.dumps([{"fields":r} for r in records]),
                '--sleep', '0.3'])
```

## 4. 大批次写需要充裕的 subprocess timeout

500-1500 条记录 + QPS 5-20 限流下，单次 CLI 调用可能跑 5-15 分钟。

公式（实测稳定）：

```python
n_chunks = (n_records + 9) // 10
timeout = max(120, n_chunks * (5 + sleep_seconds) + 60)
# 504 records → 285s
# 1500 records → 810s
```

`subprocess.run(..., timeout=120)` 默认值在批量场景下**几乎必挂**。

## 5. 删记录也是 10 条/批，且 CLI 不自动分批

`delete-records` CLI 接受逗号分隔的 record_ids 字符串，但**只删一批**——客户端必须自己分批。删 380 条 = 38 次 subprocess。

每次 60s 超时下，删 380 条至少要 38×0.5s ≈ 20s（成功路径），但若 vika 慢，60s timeout 会触发。**按需调大 delete 的 timeout 到 90s+**。

## 6. 1500 条 enterprise 体量经验性偏大

私有部署 vika 在 1500 条 × 9 字段的 enterprise 表上，列查询和插入都明显变慢。500 条左右是甜点。

> 该 demo 把 enterprise 从 50 企业 × 30 天 = 1500 砍到 30 × 14 = 420，跑得稳。

## 7. 自动占位 3 条空记录

新建 datasheet 后 `records --page-size 3` 会看到 `fields: {}` 的 3 条占位行——这是 vika 加的，不是 bug。模拟器/灌入逻辑要么忽略，要么显式删除。

## 8. 列查询慢

`records dst --page-size 1000` 在 700+ 条表上经常跑 30s+。`list_all_records` 翻页时累积更慢。给 list_records 的 timeout 至少给到 180s。

## 9. 幂等的复合主键 dedup

如果 `list_all_records` 失败（超时/错误），seeder 容易"假装表为空"然后重复插入造成 dupes。

**对策**：list 失败时**报错而不是 silently 当空表**。否则一次失败就引入大批量重复数据。

```python
# 错
try:
    existing = client.list_all_records(...)
except Exception:
    existing = []  # ← 这会导致重复插入

# 对
existing = client.list_all_records(...)  # 让异常抛出，由调用方处理
```

## 10. 字段名重命名后断链

写记录用 `fieldKey=name`（默认）的，字段在 UI 重命名后所有引用旧名的脚本断链。生产建议用 `fieldKey=id` —— `fldXXX` 形式。

---

更多见 `field-types.md`（property 格式细节）和 `fusion-api.md`（端点速查）。
