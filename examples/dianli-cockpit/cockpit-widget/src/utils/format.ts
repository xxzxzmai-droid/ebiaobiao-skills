// 数字、日期、相对时间格式化

export function formatNumber(n: number, opts?: { precision?: number; unit?: string; comma?: boolean }): string {
  const { precision = 0, unit = '', comma = true } = opts || {};
  if (n == null || isNaN(n)) return '—';
  const fixed = n.toFixed(precision);
  const display = comma ? Number(fixed).toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  }) : fixed;
  return unit ? `${display} ${unit}` : display;
}

export function formatPercent(value: number, digits = 1): string {
  if (value == null || isNaN(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

export function formatTime(value: number | string): string {
  const ts = typeof value === 'number' ? value : Date.parse(value);
  if (isNaN(ts)) return '';
  const d = new Date(ts);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function formatDateTime(value: number | string): string {
  const ts = typeof value === 'number' ? value : Date.parse(value);
  if (isNaN(ts)) return '';
  const d = new Date(ts);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function relativeTime(value: number | string): string {
  const ts = typeof value === 'number' ? value : Date.parse(value);
  if (isNaN(ts)) return '';
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60_000);
  if (m < 1) return '刚刚';
  if (m < 60) return `${m} 分钟前`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} 小时前`;
  const d = Math.floor(h / 24);
  return `${d} 天前`;
}

function pad(n: number) {
  return String(n).padStart(2, '0');
}
