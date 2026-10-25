import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/login': {
        target: 'http://localhost:8787', // URL de tu backend FastAPI
        changeOrigin: true,
        secure: false,
      },
      '^/socio(?:/|$)': {
        target: 'http://localhost:8787',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})