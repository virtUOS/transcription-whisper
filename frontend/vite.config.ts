import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Backend the dev server proxies to. Override with VITE_API_TARGET (e.g. the
// help-screenshot run points it at a separate seeded instance).
const apiTarget = process.env.VITE_API_TARGET ?? 'http://localhost:8000'
const wsTarget = apiTarget.replace(/^http/, 'ws')

export default defineConfig({
  base: process.env.VITE_BASE_PATH ? `${process.env.VITE_BASE_PATH.replace(/\/$/, '')}/` : '/',
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': apiTarget,
      '/metrics': apiTarget,
      '/api/ws': {
        target: wsTarget,
        ws: true,
      },
    },
  },
})
