# 报表开发 Skills

面向 Codex、Claude Code 等 coding agent 的 报表开发技能包。用于创建表格、处理数据、开发发布自建 Widget 小程序、编写脚本小程序和设计自动化工作流。

## 能做什么

- 创建表格、字段、视图、样例数据和业务台账。
- 查询空间站、目录、表格、字段、视图和记录。
- 批量创建、更新、删除记录，上传附件并回写。
- 开发和发布自建 Widget 小程序，适配手机、桌面和内嵌窗口。
- 编写表内脚本小程序，处理校验、查找替换、批量更新等轻量任务。
- 设计内嵌入口、后端网关和定时任务等自动化方案。

## 安装

需要 Git、Python 3、Node.js 和 npm。

macOS / Linux:

```bash
git clone https://github.com/xxzxzmai-droid/ebiaobiao-skills.git
cd ebiaobiao-skills
./install.sh --force
```

Windows PowerShell:

```powershell
git clone https://github.com/xxzxzmai-droid/ebiaobiao-skills.git
cd ebiaobiao-skills
.\install.ps1 -Force
```

默认安装到：

- `~/.codex/skills`
- `~/.claude/skills`

指定安装目录：

```bash
./install.sh --target <skills-dir> --force
```

```powershell
.\install.ps1 -Target <skills-dir> -Force
```

## 离线安装

适用于不能访问 GitHub 的环境，也适用于统信 UOS、麒麟等 Linux 桌面系统。

在可访问仓库的电脑上生成离线包：

```bash
python3 tools/package_offline.py
```

生成文件位于 `dist/`：

- `ebiaobiao-skills-offline.zip`
- `ebiaobiao-skills-offline.tar.gz`

把其中一个文件拷贝到目标电脑后解压。

macOS / Linux / 统信 UOS:

```bash
cd ebiaobiao-skills-offline
chmod +x install.sh
./install.sh --force
```

Windows PowerShell:

```powershell
cd ebiaobiao-skills-offline
.\install.ps1 -Force
```

离线包只负责安装 skills。后续如果要构建或发布 Widget 小程序，目标电脑还需要 Node.js/npm，并能访问 npm 官方源或单位内网 npm 镜像。

## 初始化

进入业务项目目录后运行：

```bash
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py init --target .
python3 ~/.codex/skills/ebiaobiao-setup/scripts/ebiao_setup.py check --target .
```

Windows 可用：

```powershell
python "$HOME\.codex\skills\ebiaobiao-setup\scripts\ebiao_setup.py" init --target .
python "$HOME\.codex\skills\ebiaobiao-setup\scripts\ebiao_setup.py" check --target .
```

部署地址不写在仓库里。初始化时如果缺少地址、API Token 或空间站 ID，脚本会打开本地配置文件，用户在本机填写 `EBIAOBIAO_HOST`、`EBIAOBIAO_API_TOKEN` 和 `EBIAOBIAO_SPACE_ID`，不要把 Token 写进对话。

## 使用

初始化完成后，直接用自然语言描述目标：

```text
使用 报表开发技能，创建一个工作督办系统，包含表格、样例数据和自建小程序。
```

```text
把当前 报表开发目标切换到财务测试空间。
```

```text
检查当前表格字段和记录，做一个批量校验并回写状态的小程序。
```

创建类需求会按固定流程执行：先问少量关键问题，再列计划，然后创建、测试、发布，最后说明创建了什么、名称是什么、在哪里查看、测试是否通过。

## 让其他 Coding Agent 使用

支持 skills 的 agent：安装后直接调用 `ebiaobiao-dev`。

不支持 skills 的 agent：让它先读仓库根目录的 `AGENTS.md`，再从 `skills/ebiaobiao-dev/SKILL.md` 开始执行。

初始化时不需要在对话里提供 Token。agent 会打开本地配置文件，用户在本机填写后继续。

多空间站配置保存在当前业务项目：

- `.env.local`：当前激活配置
- `.ebiaobiao/profiles/*.env`：已保存空间站/用户配置

这些文件只留在本机，不提交到业务项目仓库。

## 质量门

维护或交接前运行：

```bash
python3 tools/ebiao_quality_gate.py
```

只做离线检查：

```bash
python3 tools/ebiao_quality_gate.py --live never
```

同时检查 Widget 模板构建：

```bash
python3 tools/ebiao_quality_gate.py --live never --widget-build
```

质量门会检查技能结构、脚本编译、安装脚本、初始化流程、Fusion CLI dry-run、Widget 模板和文档敏感内容。只有当前配置满足开发写入条件时，才会执行真实开发空间冒烟测试。

## 更新

```bash
cd ebiaobiao-skills
git pull
./install.sh --force
```

Windows:

```powershell
cd ebiaobiao-skills
git pull
.\install.ps1 -Force
```

## 安全

- 本仓库不包含真实 Token。
- 不要在对话、截图、提交记录中暴露 Token。
- 不要提交 `.env.local` 或 `.ebiaobiao/profiles/`。
- Widget 前端不保存 Token；需要特权操作时使用本地脚本或后端服务。

## License

MIT
