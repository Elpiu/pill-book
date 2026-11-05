import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '#schema': fileURLToPath(new URL('../schema/bookpack.schema.json', import.meta.url)),
      '~': fileURLToPath(new URL('./app', import.meta.url)),
    },
  },
  test: { include: ['tests/**/*.test.ts'] },
})
