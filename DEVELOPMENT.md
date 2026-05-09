# 开发与迭代指南

这是仓库自身的开发流程。**不是 e报表使用文档**（那个看 [README.md](README.md)）。

## 本机布局（Mac）

```
~/projects/ebiaobiao-skills/         ← 工作 clone（这里改代码）
~/.claude/skills/ebiaobiao-*         ← symlink → 上面 skills/* （改了立即生效）
~/.codex/skills/ebiaobiao-*          ← 同上
```

`install.sh` 在新机器上仍是**复制**模式（拷给同事直接装就行）。本机走 dev 模式，已通过 symlink 替换好。

## 一次完整迭代

### 1. 改代码

```bash
ebiao-cd                                    # cd ~/projects/ebiaobiao-skills
# 编辑 skills/ebiaobiao-XXX/SKILL.md 或 scripts/...
```

### 2. 本地测试

跟 Claude（或 Codex）正常对话，触发 skill。改完**当前对话/下条对话立刻生效**，无需重装。

例：改完 `ebiaobiao-fusion-api/SKILL.md` 里某段，开新对话说"建一张测试表，3 个字段"，看是否按预期走。

如果一时没有合适的会话场景，跑：

```bash
ebiao-check                                  # 验证目标项目配置（在业务目录里跑）
```

### 3. 质量门（commit 前必跑）

```bash
ebiao-quality                                # 离线检查（≈3 秒，最常用）
ebiao-quality-full                           # 加上 widget npm install + build（首次或改 widget 模板时）
```

7 项检查应该全 PASS。**任何 FAIL 都不要 commit**，先修。

### 4. 提交

```bash
ebiao-cd
git status
git add <files>
git commit -m "<动词>: <做了什么>"
git push                                     # 推 origin/main
```

提交信息建议（参考已有 commit）：

- `feat: <新功能>`
- `fix: <修了什么>`
- `docs: <改文档>`
- `refactor: <重构>`
- `chore: <构建/工具>`

### 5. 同事拉新（不在本机的人）

他们：

```bash
cd /path/to/their-clone
git pull
./install.sh --force                          # 复制模式，把更新覆盖到 ~/.claude/skills/
```

或者他们也开 dev 模式（一次性）：

```bash
git clone https://github.com/xxzxzmai-droid/ebiaobiao-skills.git ~/projects/ebiaobiao-skills
for s in ebiaobiao-{dev,fusion-api,script,setup,widget,workflows}; do
  rm -rf ~/.claude/skills/$s ~/.codex/skills/$s
  ln -s ~/projects/ebiaobiao-skills/skills/$s ~/.claude/skills/$s
  ln -s ~/projects/ebiaobiao-skills/skills/$s ~/.codex/skills/$s
done
```

## 别名速查（已写入 ~/.zshrc）

| 别名 | 作用 |
|---|---|
| `ebiao-cd` | 跳到仓库 |
| `ebiao-quality` | 跑离线质量门（最常用） |
| `ebiao-quality-full` | 加上 widget npm install + build |
| `ebiao-check` | 当前业务项目的配置 self-check |
| `ebiao-pull` | 在任何目录 pull 仓库 |

变量：`$EBIAO_REPO` = `~/projects/ebiaobiao-skills`。

## 一些约定（避免踩坑）

**绝不**：

- 把真实 token / spaceId / dst id 提交到仓库（`.env.local` / `.ebiaobiao/profiles/` 已在 .gitignore）
- 在 SKILL.md / 文档里写"我们公司的 spcXXX 是 ..."
- `git commit --no-verify`（除非真的有正当理由）

**最好**：

- 改 `SKILL.md` 后跑一次 `ebiao-quality` —— frontmatter / 路径引用错了它会抓到
- 改 Python 脚本后跑 `ebiao-quality` —— compile + dry-run 检查
- 改 widget 模板后跑 `ebiao-quality-full` —— 真 npm build

## 测试 skill 触发是否准确

如果你怀疑某个 skill 的 description 不够"激进"导致漏触发，或者跟其他 skill 重叠，可以在 Claude Code 里说一些**模糊**的 prompt 看：

- "帮我做个内部数据看板" → 应触发 `ebiaobiao-widget`
- "建张表跟踪需求" → 应触发 `ebiaobiao-fusion-api`
- "在我那张数据表里写脚本批量改一下值" → 应触发 `ebiaobiao-script`
- "切换到测试空间" → 应触发 `ebiaobiao-setup`

漏触发就改对应 SKILL.md 的 description，加更多关键词（中英文都加）。

## quality gate 怎么扩

`tools/ebiao_quality_gate.py` 是单文件 Python，扩展直接在里面加 check 函数。约定：

- 函数名 `check_xxx() -> tuple[bool, str]`，返回 `(passed, message)`
- 注册到 `CHECKS` 列表
- 加完跑一次 `ebiao-quality` 看是否被纳入 summary

## 发版/Tag

目前没强制 tag 流程。如果哪天想清晰版本（比如 v0.2.0）：

```bash
ebiao-cd
git tag -a v0.2.0 -m "release: ..."
git push --tags
```

## 出问题怎么排查

| 症状 | 检查 |
|---|---|
| Claude 没识别到 skill | `ls -la ~/.claude/skills/ebiaobiao-*` 看 symlink 是不是断了 |
| skill 报路径错 | 确认仓库目录没被搬走，symlink 仍指向 `~/projects/ebiaobiao-skills` |
| `ebiao-check` 报 token missing | 业务项目目录下 `.env.local` 没填或没 export |
| 推 GitHub 401 | `git config --global user.name / user.email` 没配 |
| widget npm install 失败 | 试 `--legacy-peer-deps`，或看 `ebiao-quality-full` 输出 |

---

更多见 [AGENTS.md](AGENTS.md)（agent 视角入口）和各子 skill 的 `SKILL.md`。
