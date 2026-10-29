import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Proxies /api/* to the FastAPI server, so the browser never makes a cross-origin call (no CORS changes needed).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
});
