<script setup lang="ts">
import { db } from '~/db'

const route = useRoute()
const bookId = route.params.bookId as string
const { data: record, loaded } = useLiveQuery(() => db.books.get(bookId))
const pack = computed(() => record.value?.pack)

function normalize(text: string) {
  return text.replace(/\s+/g, ' ').trim().toLowerCase()
}

function openChapter(text: string) {
  const chapter = pack.value?.chapters.find(item => normalize(item.title) === normalize(text))
  if (chapter) navigateTo(`/book/${bookId}/ch/${chapter.id}`)
}

useHead({ title: () => `Mappa: ${pack.value?.book.title ?? 'Bookpack'}` })
</script>

<template>
  <div
    v-if="pack"
    class="flex h-dvh flex-col"
  >
    <CommonAppHeader
      title="Mappa del libro"
      :back="`/book/${bookId}`"
    />
    <p class="px-4 pb-2 text-xs text-muted">
      Tocca il titolo di un capitolo per aprirlo, il cerchio per vederne i rami. Pizzica per ingrandire.
    </p>
    <div class="min-h-0 flex-1">
      <ClientOnly>
        <SessionMindmapView
          :markdown="pack.overview.mindmap"
          :expand-level="2"
          @node-tap="openChapter"
        />
      </ClientOnly>
    </div>
  </div>
  <CommonNotFound
    v-else-if="loaded"
    message="Libro non trovato"
  />
</template>
