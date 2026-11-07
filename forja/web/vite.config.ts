import { defineConfig } from 'vite';

// base './' é obrigatório: no APK a página roda de file:///android_asset/www/index.html
export default defineConfig({
  base: './',
  // Preview em sandbox/hostnames dinâmicos: sem isto o Vite responde 403 a
  // qualquer host que não seja localhost. Afeta só o dev server, não o APK.
  server: {
    host: '0.0.0.0',
    allowedHosts: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2020',
    assetsInlineLimit: 4096,
    sourcemap: false,
    chunkSizeWarningLimit: 2048,
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts'],
  },
  define: {
    __FORJA_VERSAO__: JSON.stringify(process.env.FORJA_VERSION_NAME || '40.0.0'),
    __FORJA_COMMIT__: JSON.stringify(process.env.GITHUB_SHA || 'local'),
    __FORJA_BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
});
