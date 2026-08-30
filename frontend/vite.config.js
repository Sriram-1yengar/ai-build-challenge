import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Phase 1/2's Node server (src/server.js, port 3000) sends no CORS headers.
    // Proxying keeps that server untouched instead of reaching into someone
    // else's service to add CORS — see structure.md ground rule 1.
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
})
