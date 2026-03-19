import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
      '/api/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
