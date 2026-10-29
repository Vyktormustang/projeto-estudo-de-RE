import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: true,
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    target: 'es2019',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes('node_modules/chess.js') ||
            id.includes('/src/engine/chess/')
          ) {
            return 'forja-chess';
          }
          if (id.includes('node_modules')) {
            return 'vendor';
          }
          if (id.includes('/src/engine/teachingsSovereignty40')) {
            return 'forja-codex-vol3';
          }
          if (id.includes('/src/engine/teachingsBicentenary40')) {
            return 'forja-codex-vol2';
          }
          if (
            id.includes('/src/engine/teachingsCatalog') ||
            id.includes('/src/engine/polymathRadarEngine')
          ) {
            return 'forja-codex-160';
          }
          if (id.includes('/src/engine/')) {
            return 'forja-core';
          }
          return undefined;
        },
      },
    },
  },
});
