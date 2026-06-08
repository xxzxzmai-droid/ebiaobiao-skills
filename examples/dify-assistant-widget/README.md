# dify-assistant-widget — 把 Dify 智能体做成 e报表小程序

一个最小的 e报表（vika/APITable）自建小程序：用 `iframe` 把一个 **Dify chatflow 智能体**嵌进空间站，让用户在 e报表里直接对话。小程序本身只是个薄壳（一个 React 组件 + app-shell CSS），智能体逻辑全在 Dify 侧。

配套技能：`skills/ebiaobiao-widget`（见其「Recipe: embed a Dify chatflow as a widget」与 Gotcha 7）。

## 它解决/暴露的关键问题

1. **自签证书 / 混合内容是硬门槛。** 小程序在用户浏览器里跑（e报表 是 https），要显示对话就得浏览器**直接**打开 Dify 地址——小程序没有服务端反代。若 Dify 是内网 IP + 自签证书（常见，如 `https://10.x.x.x:5030`），浏览器会**静默**拦掉 iframe（证书不受信 + 混合内容），一片空白，且 `iframe` **不触发** `onError`，JS 测不出来。
   - 根治：用有效证书把 Dify 暴露到浏览器可达的地址。
   - 兜底（内网自签）：用户先在新标签打开 Dify 源、点「继续访问(不安全)」登记证书例外，再回小程序「重新加载」。组件已内置这条引导栏。
2. **不写死地址。** Dify 地址 / token / 嵌入路径 / 可选演示身份全部用 `useCloudStorage` 存在空间里（管理员设一次），`useSettingsButton` 出设置面板。源码零外链。
3. **app-shell 布局。** flex 列：固定头部 + 证书提示条（`flex-shrink:0`）+ iframe 填满 `flex:1; min-height:0` 中段。不用 `100vh` / `position:sticky`。

## 文件

- `src/widget.tsx` — 入口，`initializeWidget(DifyAssistantWidget, '<packageId>')`。
- `src/DifyAssistantWidget.tsx` — 主组件：iframe + 设置面板 + 证书引导。
- `src/styles.css` — app-shell 布局。
- `widget.config.json` — `packageId`（须 `wpk[A-Za-z0-9]{10}`）、`spaceId`、`sandbox: true`。

> 注意：`package_icon.png` / `cover.png` / `author_icon.png` 未随例子提交（二进制）。发布前放三张图到本目录，或复用任意现成图标。

## 跑起来

```bash
npm install
npm run typecheck          # tsc 类型检查
# 发布到空间站（首次新包：版本走 --version、create-package 用管道 Y、不要 --ci，见 Gotcha 7）：
export VIKA_API_TOKEN=usk********
NODE_TLS_REJECT_UNAUTHORIZED=0 bash -c 'printf "Y\n" | widget-cli release --version 0.1.0 \
  --host https://<你的e报表host>:7886 --uploadHost https://<同上> --token "$VIKA_API_TOKEN"'
```

输出里要看到 `Successful create widgetPackage from server` → `Compile Succeed` → `successful release`，否则包没注册到空间。

## 已上线参考

生产空间 `spcjCWa40legH` 已发布 `wpkMatAssist1`（「物资智能助手」），即由本例脚手架而来。

> `vite build` 在新版 vite/rolldown 下可能报 `failed to resolve "@apitable/widget-sdk"`——那是 rolldown 与 apitable SDK 包结构的兼容问题，与发布无关：`widget-cli release` 用自带 webpack 打包，`tsc --noEmit` 通过即可。
