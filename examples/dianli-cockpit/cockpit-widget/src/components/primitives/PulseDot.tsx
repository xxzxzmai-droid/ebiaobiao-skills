import React from 'react';

interface PulseDotProps {
  color: string;
  size?: number;
}

/** 呼吸/脉动小圆点。用于"实时""红色预警进行中"等状态。 */
export const PulseDot: React.FC<PulseDotProps> = ({ color, size = 8 }) => (
  <span
    style={{
      display: 'inline-block',
      width: size,
      height: size,
      borderRadius: '50%',
      backgroundColor: color,
      boxShadow: `0 0 ${size}px ${color}`,
      animation: 'pulseDot 1.6s ease-in-out infinite',
    }}
  />
);

// 配套的 keyframes 在 style.css 里：
//   @keyframes pulseDot { 0%, 100% { opacity: 1 } 50% { opacity: 0.35 } }
