<script setup lang="ts">
const { items, resume, loaded, error } = useLibrary()
const { app } = useRuntimeConfig()
const sampleUrl = `${app.baseURL}samples/how-to-live-on-24-hours-a-day.bookpack.json`
</script>

<template>
  <div class="mx-auto min-h-dvh max-w-2xl pb-24">
    <CommonAppHeader title="Bookpack">
      <UButton
        to="/settings"
        icon="i-lucide-settings"
        color="neutral"
        variant="ghost"
        size="lg"
        aria-label="Impostazioni"
      />
    </CommonAppHeader>

    <main class="space-y-5 px-4 pt-2">
      <UAlert
        v-if="error"
        color="error"
        title="Impossibile leggere la libreria"
        description="Il browser non permette di accedere ai dati locali. Controlla che non sia attiva la navigazione privata."
      />

      <NuxtLink
        v-if="resume"
        :to="`/book/${resume.item.record.id}/ch/${resume.chapter.id}`"
        class="block rounded-2xl bg-primary p-5 text-inverted transition hover:opacity-95 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        <p class="flex items-center gap-2 text-sm font-semibold opacity-90">
          <UIcon
            name="i-lucide-play"
            class="size-4"
            aria-hidden="true"
          />
          Riprendi
        </p>
        <p class="mt-2 line-clamp-2 font-serif text-xl leading-snug font-semibold">
          {{ resume.chapter.title }}
        </p>
        <p class="mt-1 truncate text-sm opacity-90">
          {{ resume.item.record.pack.book.title }}
        </p>
        <p class="text-sm opacity-90">
          {{ resume.label }}
        </p>
      </NuxtLink>

      <div
        v-if="items.length"
        class="space-y-3"
      >
        <BookCard
          v-for="item in items"
          :key="item.record.id"
          :item="item"
        />
      </div>

      <UEmpty
        v-else-if="loaded && !error"
        class="pt-16"
        icon="i-lucide-library"
        title="La tua libreria è vuota"
        description="Importa un book pack generato con la CLI, oppure prova il libro d'esempio per vedere come funziona."
        :actions="[
          { label: 'Importa un libro', to: '/import', icon: 'i-lucide-plus' },
          { label: 'Prova l\'esempio', to: { path: '/import', query: { url: sampleUrl } }, color: 'neutral', variant: 'subtle' },
        ]"
      />
    </main>

    <div
      v-if="items.length"
      class="pointer-events-none fixed inset-x-0 bottom-0 flex justify-center pb-[max(1rem,env(safe-area-inset-bottom))]"
    >
      <UButton
        to="/import"
        icon="i-lucide-plus"
        size="xl"
        label="Importa"
        class="pointer-events-auto rounded-full shadow-lg"
      />
    </div>
  </div>
</template>
