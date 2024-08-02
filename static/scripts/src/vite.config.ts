import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    assetsDir: '',
    manifest: true,
    rollupOptions: {
      input: 'src/main.tsx',
      output: {
        entryFileNames: 'main.js', // This line sets the output file name for the entry chunk
        chunkFileNames: '[name].js', // Optional: Sets a pattern for chunk files, if needed
        assetFileNames: '[name].[ext]' // Optional: Sets a pattern for asset files, if needed
      }
    }
  }
})
