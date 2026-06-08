import React, { useMemo, useState } from 'react';
import { useCloudStorage, useSettingsButton } from '@apitable/widget-sdk';

/**
 * 物资智能助手 e报表小程序
 *
 * 形态：在 e报表空间站里以 iframe 嵌入物资管理 Dify chatflow 智能体。
 * 配置：Dify 地址 / 对话 token / 嵌入路径 / 可选演示身份，全部存在小程序云存储
 *       （useCloudStorage，空间内共享、管理员设一次即可），不写死任何外链。
 *
 * 自签证书坑：宿主是 e报表（https），Dify 多为内网自签证书。浏览器会以
 *   「混合内容 / 证书不受信」静默拦掉 iframe（一片空白、且不触发 onError）。
 *   解法：首次使用先在新标签打开 Dify 地址、点「继续访问(不安全)」让浏览器
 *   记住该来源的证书例外，再回到小程序点「重新加载」。根治办法是用有效证书
 *   把 Dify 暴露出来。
 *
 * 布局：严格遵循 e报表小程序 app-shell（flex 列 + 唯一滚动中段），
 *   宿主 iframe 高度受控且 overflow:hidden，不能依赖 body 滚动 / sticky。
 */

type EmbedPath = 'chatbot' | 'chat';

// 开箱默认（可在「设置」里覆盖）：指向本部署的 Dify。token 为 Dify 公开 embed token，非密钥。
// 注意：内网自签证书地址，浏览器首次需信任证书后 iframe 才会加载（见顶部证书提示条）。
const DEFAULT_DIFY_BASE = 'https://10.134.252.232:5030/dify';
const DEFAULT_DIFY_TOKEN = 'e8YydeOGAYYIBAi4';

function trimUrl(u: string): string {
  return (u || '').trim().replace(/\/+$/, '');
}

/** 拼 Dify 嵌入 URL：`<base>/<path>/<token>` + 可选明文身份参数。 */
function buildSrc(
  base: string,
  token: string,
  path: EmbedPath,
  role: string,
  orgId: string,
  orgName: string,
): string {
  const b = trimUrl(base);
  const t = (token || '').trim();
  if (!b || !t) return '';
  let url = `${b}/${path}/${encodeURIComponent(t)}`;
  const params: string[] = [];
  if (role) params.push('mat_role=' + encodeURIComponent(role));
  if (orgId) params.push('mat_org_id=' + encodeURIComponent(orgId));
  if (orgName) params.push('mat_org_name=' + encodeURIComponent(orgName));
  if (params.length) url += '?' + params.join('&');
  return url;
}

export const DifyAssistantWidget: React.FC = () => {
  // 顶部设置按钮：返回 [是否显示设置, 切换函数]
  const [isShowingSettings] = useSettingsButton();

  // 配置项（空间内持久共享）；editable 表示当前用户是否有写权限。
  const [baseUrl, setBaseUrl, editable] = useCloudStorage<string>('difyBaseUrl', DEFAULT_DIFY_BASE);
  const [token, setToken] = useCloudStorage<string>('difyToken', DEFAULT_DIFY_TOKEN);
  const [embedPath, setEmbedPath] = useCloudStorage<EmbedPath>('difyEmbedPath', 'chatbot');
  const [demoRole, setDemoRole] = useCloudStorage<string>('difyDemoRole', '');
  const [demoOrgId, setDemoOrgId] = useCloudStorage<string>('difyDemoOrgId', '');
  const [demoOrgName, setDemoOrgName] = useCloudStorage<string>('difyDemoOrgName', '');

  // 改一次 src 的 key，用于「重新加载」强制刷新 iframe。
  const [reloadKey, setReloadKey] = useState(0);

  const src = useMemo(
    () => buildSrc(baseUrl, token, embedPath, demoRole, demoOrgId, demoOrgName),
    [baseUrl, token, embedPath, demoRole, demoOrgId, demoOrgName],
  );

  const difyOrigin = trimUrl(baseUrl);
  const configured = Boolean(src);

  return (
    <div className="assist-root">
      {/* 顶栏（固定高度，绝不滚走） */}
      <header className="assist-header">
        <div className="assist-title">
          <span className="assist-dot" />
          物资智能助手
        </div>
        <div className="assist-header-actions">
          {configured && (
            <button className="assist-btn" onClick={() => setReloadKey((k) => k + 1)}>
              重新加载
            </button>
          )}
        </div>
      </header>

      {/* 自签证书提示条（仅在已配置且为 https 内网地址时给出引导） */}
      {configured && (
        <div className="assist-certbar">
          首次空白？多半是 Dify 自签证书未被浏览器信任 ——
          <a href={difyOrigin} target="_blank" rel="noreferrer" className="assist-link">
            ① 新标签打开 Dify 并点「继续访问」
          </a>
          <button className="assist-link assist-linkbtn" onClick={() => setReloadKey((k) => k + 1)}>
            ② 回来点「重新加载」
          </button>
        </div>
      )}

      {/* 唯一滚动/内容中段 */}
      <main className="assist-body">
        {isShowingSettings ? (
          <SettingsPanel
            editable={editable}
            baseUrl={baseUrl}
            token={token}
            embedPath={embedPath}
            demoRole={demoRole}
            demoOrgId={demoOrgId}
            demoOrgName={demoOrgName}
            onChange={{
              setBaseUrl,
              setToken,
              setEmbedPath,
              setDemoRole,
              setDemoOrgId,
              setDemoOrgName,
            }}
          />
        ) : configured ? (
          <iframe
            key={reloadKey}
            className="assist-iframe"
            src={src}
            title="物资智能助手"
            allow="microphone; clipboard-write"
          />
        ) : (
          <EmptyState editable={editable} />
        )}
      </main>
    </div>
  );
};

const EmptyState: React.FC<{ editable: boolean }> = ({ editable }) => (
  <div className="assist-empty">
    <div className="assist-empty-icon">🤖</div>
    <div className="assist-empty-title">尚未配置 Dify 智能体</div>
    <p className="assist-empty-text">
      {editable
        ? '点击右上角「设置」按钮，填写 Dify 地址与对话 token 即可启用。'
        : '请联系空间站管理员在小程序「设置」里配置 Dify 地址与 token。'}
    </p>
  </div>
);

type Setters = {
  setBaseUrl: (v: string) => void;
  setToken: (v: string) => void;
  setEmbedPath: (v: EmbedPath) => void;
  setDemoRole: (v: string) => void;
  setDemoOrgId: (v: string) => void;
  setDemoOrgName: (v: string) => void;
};

const SettingsPanel: React.FC<{
  editable: boolean;
  baseUrl: string;
  token: string;
  embedPath: EmbedPath;
  demoRole: string;
  demoOrgId: string;
  demoOrgName: string;
  onChange: Setters;
}> = ({ editable, baseUrl, token, embedPath, demoRole, demoOrgId, demoOrgName, onChange }) => (
  <div className="assist-settings">
    {!editable && (
      <div className="assist-note">你没有该小程序的写权限，以下配置只读。</div>
    )}
    <label className="assist-field">
      <span>Dify 地址（base）</span>
      <input
        disabled={!editable}
        value={baseUrl}
        placeholder="https://你的dify域名 （如 https://dify.example.com）"
        onChange={(e) => onChange.setBaseUrl(e.target.value)}
      />
      <small>不要带末尾斜杠。内网自签地址可用，但浏览器需先信任其证书。</small>
    </label>
    <label className="assist-field">
      <span>对话 token</span>
      <input
        disabled={!editable}
        value={token}
        placeholder="Dify 应用的公开 chatbot/chat token"
        onChange={(e) => onChange.setToken(e.target.value)}
      />
    </label>
    <label className="assist-field">
      <span>嵌入路径</span>
      <select
        disabled={!editable}
        value={embedPath}
        onChange={(e) => onChange.setEmbedPath(e.target.value as EmbedPath)}
      >
        <option value="chatbot">chatbot（标准嵌入）</option>
        <option value="chat">chat（兼容，明文身份参数）</option>
      </select>
    </label>
    <div className="assist-subhead">可选 · 演示身份（留空 = 智能体按默认演示账号）</div>
    <label className="assist-field">
      <span>mat_role</span>
      <input
        disabled={!editable}
        value={demoRole}
        placeholder="department_admin / area_admin / city_admin"
        onChange={(e) => onChange.setDemoRole(e.target.value)}
      />
    </label>
    <label className="assist-field">
      <span>mat_org_id</span>
      <input
        disabled={!editable}
        value={demoOrgId}
        placeholder="所属机构 org_id（演示部门账号填其 org）"
        onChange={(e) => onChange.setDemoOrgId(e.target.value)}
      />
    </label>
    <label className="assist-field">
      <span>mat_org_name</span>
      <input
        disabled={!editable}
        value={demoOrgName}
        placeholder="机构展示名"
        onChange={(e) => onChange.setDemoOrgName(e.target.value)}
      />
    </label>
    <div className="assist-note">
      身份参数仅在「chat」路径以明文附加；「chatbot」标准嵌入默认走智能体内置演示身份。
    </div>
  </div>
);
