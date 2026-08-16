import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

console.log('vitest config loaded from:', __dirname)

export default defineConfig({
  plugins: [
    react(),
  ],
  resolve: {
    tsconfigPaths: true, // Native tsconfig paths resolution
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    include: ['**/*.{test,spec}.{ts,tsx}'],
    exclude: [
      'node_modules',
      '.next',
      'playwright/**',
      'tests/**',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        '.next/',
        'tests/**',
        '**/*.config.*',
        '**/types/**',
      ],
    },
  },
})
