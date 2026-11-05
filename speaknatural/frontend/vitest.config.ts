import { defineConfig } from 'vitest/config';

/** Configuração só dos testes unitários (npm test). */
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
