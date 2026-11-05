import { fileURLToPath } from 'node:url'

// Su GitHub Pages l'app vive in una sottocartella: si imposta con NUXT_APP_BASE_URL=/nome-repo/
const baseURL = process.env.NUXT_APP_BASE_URL || '/'

export default defineNuxtConfig({
  modules: ['@nuxt/ui', '@nuxt/eslint', '@vite-pwa/nuxt'],
  ssr: false,
  devtools: { enabled: false },
  app: {
    head: {
      title: 'Bookpack',
      htmlAttrs: { lang: 'it' },
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        { name: 'description', content: 'Libri condensati in pillole: card, mindmap e flashcard.' },
        { name: 'theme-color', content: '#0f766e' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: `${baseURL}icon.svg` },
        { rel: 'apple-touch-icon', href: `${baseURL}apple-touch-icon.png` },
      ],
    },
  },
  css: ['~/assets/css/main.css'],
  alias: {
    '#schema': fileURLToPath(new URL('../schema/bookpack.schema.json', import.meta.url)),
  },
  // I font arrivano da Fontsource e le icone sono nel bundle: l'app non chiede nulla alla rete
  ui: { fonts: false },
  icon: {
    provider: 'none',
    fallbackToApi: false,
    clientBundle: {
      scan: true,
      // Icone usate internamente dai componenti di Nuxt UI
      icons: [
        'lucide:arrow-left', 'lucide:arrow-right', 'lucide:check', 'lucide:chevron-down',
        'lucide:chevron-left', 'lucide:chevron-right', 'lucide:chevron-up', 'lucide:circle-alert',
        'lucide:circle-check', 'lucide:circle-x', 'lucide:file', 'lucide:info',
        'lucide:loader-circle', 'lucide:minus', 'lucide:plus', 'lucide:triangle-alert',
        'lucide:upload', 'lucide:x',
      ],
    },
  },
  compatibilityDate: '2026-11-01',
  vite: {
    server: { fs: { allow: ['..'] } },
  },
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'Bookpack',
      short_name: 'Bookpack',
      description: 'Libri condensati in pillole: card, mindmap e flashcard.',
      lang: 'it',
      theme_color: '#0f766e',
      background_color: '#fafaf9',
      display: 'standalone',
      orientation: 'portrait',
      start_url: baseURL,
      scope: baseURL,
      icons: [
        { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
        { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
        { src: 'pwa-maskable-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    workbox: {
      navigateFallback: baseURL,
      globPatterns: ['**/*.{js,css,html,json,png,svg,woff2}'],
      globIgnores: [
        // Gli alfabeti non latini non servono offline: restano scaricabili quando c'è rete
        '**/*cyrillic*', '**/*greek*', '**/*vietnamese*',
        // Copie della stessa shell: basta index.html con navigateFallback. Precaricarle farebbe
        // fallire l'installazione sugli host che non servono URL come /404 o /import.
        '200.html', '404.html', 'import/**', 'settings/**',
      ],
      maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
    },
    client: { installPrompt: false },
    devOptions: { enabled: false },
  },
})
