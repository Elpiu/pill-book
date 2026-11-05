<script setup lang="ts">
import { db } from '~/db'
import { bookPercent, nextChapter } from '~/utils/progress'
import { totalMinutes } from '~/utils/validatePack'

const route = useRoute()
const bookId = route.params.bookId as string

const { data, loaded } = useLiveQuery(async () => {
  const [record, progress] = await Promise.all([db.books.get(bookId), db.progress.get(bookId)])
  return { record, progress }
})

const pack = computed(() => data.value?.record?.pack)
const progress = computed(() => data.value?.progress)
const percent = computed(() => (pack.value ? bookPercent(pack.value, progress.value) : 0))
const suggested = computed(() => (pack.value ? nextChapter(pack.value, progress.value) : undefined))
const glossaryOpen = ref(false)

useHead({ title: () => pack.value?.book.title ?? 'Bookpack' })
</script>

<template>
  <div v-if="pack">
    <div class="mx-auto min-h-dvh max-w-2xl pb-10">
      <CommonAppHeader
        :title="pack.book.title"
        back="/"
      />

      <main class="space-y-5 px-4 pt-2">
        <div class="flex gap-4">
          <BookCover
            :color="pack.book.coverColor"
            :title="pack.book.title"
            class="h-32 w-22 shrink-0"
          />
          <div class="flex min-w-0 flex-1 flex-col">
            <h2 class="font-serif text-2xl leading-tight font-semibold">
              {{ pack.book.title }}
            </h2>
            <p
              v-if="pack.book.author"
              class="mt-1 text-muted"
            >
              {{ pack.book.author }}
            </p>
            <p class="mt-1 text-sm text-muted">
              {{ pack.chapters.length }} capitoli · {{ totalMinutes(pack) }} min
            </p>
            <div class="mt-auto pt-2">
              <UProgress
                :model-value="percent"
                size="sm"
                :aria-label="`Letto al ${percent}%`"
              />
              <p class="mt-1 text-xs text-muted">
                {{ percent }}% completato
              </p>
            </div>
          </div>
        </div>

        <BookOverviewPanel :overview="pack.overview" />

        <div class="flex flex-wrap gap-2">
          <UButton
            :to="`/book/${bookId}/map`"
            icon="i-lucide-network"
            color="neutral"
            variant="subtle"
            label="Mappa del libro"
          />
          <UButton
            v-if="pack.glossary?.length"
            icon="i-lucide-book-a"
            color="neutral"
            variant="subtle"
            label="Glossario"
            @click="glossaryOpen = true"
          />
        </div>

        <section aria-label="Percorso">
          <h2 class="mb-3 text-sm font-semibold text-muted">
            Percorso
          </h2>
          <ol>
            <BookChapterStep
              v-for="(chapter, i) in pack.chapters"
              :key="chapter.id"
              :book-id="bookId"
              :chapter="chapter"
              :progress="progress"
              :suggested="chapter.id === suggested?.id"
              :last="i === pack.chapters.length - 1"
            />
          </ol>
          <p
            v-if="!suggested"
            class="pt-1 text-center text-sm text-muted"
          >
            Hai completato tutti i capitoli. Puoi rileggerli quando vuoi.
          </p>
        </section>
      </main>
    </div>

    <UModal
      v-if="pack.glossary?.length"
      v-model:open="glossaryOpen"
      title="Glossario"
      :description="pack.book.title"
    >
      <template #body>
        <dl class="space-y-4">
          <div
            v-for="entry in pack.glossary"
            :key="entry.term"
          >
            <dt class="font-serif font-semibold">
              {{ entry.term }}
            </dt>
            <dd class="text-sm text-muted">
              {{ entry.definition }}
            </dd>
          </div>
        </dl>
      </template>
    </UModal>
  </div>
  <CommonNotFound
    v-else-if="loaded"
    message="Libro non trovato"
  />
</template>
