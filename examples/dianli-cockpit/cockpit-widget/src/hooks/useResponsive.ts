import { useEffect, useState } from 'react';
import { BREAKPOINT_MOBILE, BREAKPOINT_NARROW, BREAKPOINT_BIG_SCREEN } from '../constants';

export interface Responsive {
  width: number;
  height: number;
  /** width < 480 — 手机/企微 panel/桌面侧边栏 */
  isMobile: boolean;
  /** width < 768 — 紧凑模式 */
  isNarrow: boolean;
  /** width >= 1600 — 大屏模式（4 行经典布局）*/
  isBigScreen: boolean;
}

/**
 * 监测容器宽高变化，决定大屏 / 紧凑 / 手机三档布局。
 *
 * widget 在 vika iframe 里跑，window 尺寸跟实际容器可能不一致——
 * 用 ResizeObserver 监听 document.body 更准。
 */
export function useResponsive(): Responsive {
  const [size, setSize] = useState<{ width: number; height: number }>(() => ({
    width: typeof window !== 'undefined' ? window.innerWidth : 1200,
    height: typeof window !== 'undefined' ? window.innerHeight : 800,
  }));

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const target = document.body;

    const update = (w: number, h: number) => {
      setSize((prev) =>
        prev.width === w && prev.height === h ? prev : { width: w, height: h },
      );
    };

    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver((entries) => {
        const e = entries[0];
        if (!e) return;
        update(Math.round(e.contentRect.width), Math.round(e.contentRect.height));
      });
      ro.observe(target);
    }
    const onResize = () => update(window.innerWidth, window.innerHeight);
    window.addEventListener('resize', onResize);
    onResize();
    return () => {
      if (ro) ro.disconnect();
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return {
    width: size.width,
    height: size.height,
    isMobile: size.width < BREAKPOINT_MOBILE,
    isNarrow: size.width < BREAKPOINT_NARROW,
    isBigScreen: size.width >= BREAKPOINT_BIG_SCREEN,
  };
}
