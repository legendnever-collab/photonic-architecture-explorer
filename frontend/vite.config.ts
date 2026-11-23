import { defineConfig } from 'vite';

// The built Workspace ships inside the Python package so users never need Node.
export default defineConfig({
  base: './',
  build: {
    outDir: '../src/photonic_architecture_explorer/web',
    emptyOutDir: true,
    target: 'es2022',
    chunkSizeWarningLimit: 1200,
    rollupOptions: { output: { entryFileNames: 'assets/app.js', chunkFileNames: 'assets/[name].js', assetFileNames: 'assets/[name][extname]' } },
  },
  server: { proxy: { '/api': 'http://127.0.0.1:8770' } },
});
