import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Configuração do Vite (servidor de desenvolvimento e build).
 *
 * - base: './'  -> obrigatório para o APK (Capacitor abre os arquivos via
 *                  file://, então as URLs não podem começar com "/").
 * - server.proxy -> no PC, o app em http://localhost:5173 chama "/api" e o
 *                  Vite repassa para o Python em http://localhost:8000.
 *                  No celular (APK) não existe proxy: o app chama o IP do PC
 *                  direto (configurado na tela "Servidor").
 * - allowedHosts -> libera o domínio de preview (https://...e2b.app).
 */
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    allowedHosts: true,
    // O projeto Android fica nesta pasta; sem isso o Vite recarrega a página
    // toda vez que o `cap sync` copia o dist para dentro do APK.
    watch: { ignored: ['**/android/**', '**/resources/**'] },
    proxy: {
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/sentences': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/analyze': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/history': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/docs': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/openapi.json': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    allowedHosts: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    target: 'es2019',
  },
});
