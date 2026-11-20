import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' para que el build funcione desde cualquier ruta (la app se publica en una subruta).
// En desarrollo, /api se redirige a Uvicorn. Se usa 127.0.0.1 y no localhost: en Windows,
// localhost intenta primero IPv6 y cada petición tardaba ~2 s.
export default defineConfig({
  base: './',
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
