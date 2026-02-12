import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const basePath = process.env.VITE_BASE_PATH || '/team8/'
const normalizedBase = basePath.endsWith('/') ? basePath : `${basePath}/`

export default defineConfig({
  plugins: [react()],
  base: normalizedBase,
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        // Backend in dev (adjust if you run it elsewhere)
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
})
