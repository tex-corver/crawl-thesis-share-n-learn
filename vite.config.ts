import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    allowedHosts: [
      '.ngrok-free.dev',
      '.trycloudflare.com',
      '.loca.lt',
    ],
  },
})
