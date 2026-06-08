import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2018',
    cssTarget: 'chrome61',
  },
  server: {
    host: '127.0.0.1',
    port: 5190,
    fs: {
      allow: ['..'],
    },
  },
});
