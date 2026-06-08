import React, { useMemo, useState } from 'react';
import { useCloudStorage, useSettingsButton } from '@apitable/widget-sdk';

/**
 * 物资智能助手 e报表小程序
 *
 * 布局：根容器 position:fixed inset:0 铺满整个小程序 iframe（不依赖 height:100% 链，
 *   避免宿主不给定高时塌成一条）；细顶栏 flex-shrink:0；对话 iframe 用 absolute inset:0
 *   填满中段。证书提示收进 ⓘ 图标按需展开，默认不占地方。
 *
 * 配置：Dify 地址 / token / 路径 / 演示身份存 useCloudStorage（空间共享）；
 *   已预填默认 Dify 地址与 embed token，装上即用。
 */

type EmbedPath = 'chatbot' | 'chat';

// 开箱默认（可在「设置」覆盖）。token 为 Dify 公开 embed token，非密钥。
const DEFAULT_DIFY_BASE = 'https://10.134.252.232:5030/dify';
const DEFAULT_DIFY_TOKEN = 'e8YydeOGAYYIBAi4';

function trimUrl(u: string): string {
  return (u || '').trim().replace(/\/+$/, '');
}

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
  const [isShowingSettings] = useSettingsButton();

  const [baseUrl, setBaseUrl, editable] = useCloudStorage<string>('difyBaseUrl', DEFAULT_DIFY_BASE);
  const [token, setToken] = useCloudStorage<string>('difyToken', DEFAULT_DIFY_TOKEN);
  const [embedPath, setEmbedPath] = useCloudStorage<EmbedPath>('difyEmbedPath', 'chatbot');
  const [demoRole, setDemoRole] = useCloudStorage<string>('difyDemoRole', '');
  const [demoOrgId, setDemoOrgId] = useCloudStorage<string>('difyDemoOrgId', '');
  const [demoOrgName, setDemoOrgName] = useCloudStorage<string>('difyDemoOrgName', '');

  const [reloadKey, setReloadKey] = useState(0);
  const [showTip, setShowTip] = useState(false);

  const src = useMemo(
    () => buildSrc(baseUrl, token, embedPath, demoRole, demoOrgId, demoOrgName),
    [baseUrl, token, embedPath, demoRole, demoOrgId, demoOrgName],
  );
  const difyOrigin = trimUrl(baseUrl);
  const configured = Boolean(src);

  return (
    <div className="assist-root">
      {/* 细顶栏 */}
      <header className="assist-bar">
        <span className="assist-title">
          <span className="assist-dot" />
          物资智能助手
        </span>
        {configured && !isShowingSettings && (
          <span className="assist-tools">
            <button className="assist-icon" title="重新加载" onClick={() => setReloadKey((k) => k + 1)}>
              ⟳
            </button>
            <button
              className={'assist-icon' + (showTip ? ' assist-icon--on' : '')}
              title="空白？证书帮助"
              onClick={() => setShowTip((s) => !s)}
            >
              ⓘ
            </button>
          </span>
        )}
      </header>

      {/* 证书提示：默认收起，点 ⓘ 展开 */}
      {showTip && configured && !isShowingSettings && (
        <div className="assist-tip">
          面板空白多为 Dify 自签证书未被信任：
          <a href={difyOrigin} target="_blank" rel="noreferrer">
            新标签打开 Dify → 点「继续访问」
          </a>
          ，再点 ⟳ 重新加载。
        </div>
      )}

      {/* 内容中段：iframe / 设置 / 空态 均绝对铺满 */}
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
            onChange={{ setBaseUrl, setToken, setEmbedPath, setDemoRole, setDemoOrgId, setDemoOrgName }}
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
    {!editable && <div className="assist-note">你没有该小程序的写权限，以下配置只读。</div>}
    <label className="assist-field">
      <span>Dify 地址（base）</span>
      <input
        disabled={!editable}
        value={baseUrl}
        placeholder="https://你的dify域名/dify"
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
        placeholder="所属机构 org_id"
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
    <div className="assist-note">身份参数仅在「chat」路径以明文附加；「chatbot」走智能体内置演示身份。</div>
  </div>
);
