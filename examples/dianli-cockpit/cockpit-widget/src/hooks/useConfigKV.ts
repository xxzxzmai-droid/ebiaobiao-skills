import { useMemo } from 'react';

/**
 * 从配置参数表（key/value 二列）里读 KV。
 * 调用方传 config records（来自 useCockpitData().config）即可。
 */
export function useConfigKV(records: Array<Record<string, unknown>>) {
  return useMemo(() => {
    const kv: Record<string, string> = {};
    for (const r of records) {
      const k = r['标题'] as string | undefined;
      const v = r['值'] as string | undefined;
      if (k && v != null) kv[k] = String(v);
    }
    return {
      raw: kv,
      get: (key: string, fallback = ''): string => kv[key] ?? fallback,
      getNumber: (key: string, fallback = 0): number => {
        const v = kv[key];
        if (v == null) return fallback;
        const n = parseFloat(v);
        return isNaN(n) ? fallback : n;
      },
    };
  }, [records]);
}
