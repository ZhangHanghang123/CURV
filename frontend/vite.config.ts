import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.VITE_API_TARGET || 'http://127.0.0.1:8003'

export default defineConfig({
  plugins: [react()],
  base: '/curv/',
  server: {
    port: 5174,
    proxy: {
      '/curv/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/curv/, ''),
      },
    },
  },
  build: {
    emptyOutDir: false,
  },
})