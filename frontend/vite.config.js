import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // The browser talks to Vite, Vite forwards /api calls to FastAPI. No CORS problems.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})