<script setup lang="ts">
import { chapterAfter } from '~/utils/progress'

const route = useRoute()
const bookId = route.params.bookId as string
const chapterId = route.params.chId as string

const session = useSession(bookId, chapterId)
const { status, pack, chapter, phase, cardIndex, flashResults, percent, isReview } = session

onMounted(session.load)

const next = computed(() => (pack.value ? chapterAfter(pack.value, chapterId) : undefined))
const position = computed(() => {
  if (!chapter.value) return ''
  switch (phase.value) {
    case 'cards': return `Card ${cardIndex.value + 1} di ${chapter.value.cards.length}`
    case 'mindmap': return 'Mindmap'
    case 'flashcards': return 'Flashcard'
    default: return 'Completato'
  }
})

function onMindmapKey(event: KeyboardEvent) {
  if (phase.value !== 'mindmap') return
  if (event.key === 'ArrowRight') session.goToPhase('flashcards')
  else if (event.key === 'ArrowLeft') session.goToPhase('cards')
}

onMounted(() => window.addEventListener('keydown', onMindmapKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onMindmapKey))

useHead({ title: () => chapter.value?.title ?? 'Bookpack' })
</script>

<template>
  <CommonNotFound
    v-if="status === 'missing'"
    message="Capitolo non trovato"
  />

  <div
    v-else-if="status === 'ready' && chapter"
    class="fixed inset-0 flex flex-col overscroll-none"
  >
    <header class="safe-top flex items-center gap-2 px-2 pb-3">
      <UButton
        :to="`/book/${bookId}`"
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="lg"
        aria-label="Chiudi e torna al percorso"
      />
      <div class="min-w-0 flex-1">
        <p class="truncate text-sm font-medium">
          {{ chapter.title }}
        </p>
        <p
          class="text-xs text-muted"
          data-testid="session-position"
        >
          {{ position }}<template v-if="isReview">
            · Rilettura
          </template>
        </p>
      </div>
      <span class="w-3" />
    </header>
    <UProgress
      :model-value="percent"
      size="xs"
      class="px-4 pb-3"
      :aria-label="`Avanzamento della sessione: ${percent}%`"
    />

    <main class="min-h-0 flex-1">
      <SessionCardDeck
        v-if="phase === 'cards'"
        class="safe-bottom"
        :cards="chapter.cards"
        :start-index="cardIndex"
        @change="session.setCard"
        @finished="session.goToPhase('mindmap')"
      />

      <div
        v-else-if="phase === 'mindmap'"
        class="flex h-full flex-col"
      >
        <div class="min-h-0 flex-1">
          <ClientOnly>
            <SessionMindmapView :markdown="chapter.mindmap" />
          </ClientOnly>
        </div>
        <div class="safe-bottom grid grid-cols-[auto_1fr] gap-3 px-4 pt-3">
          <UButton
            size="xl"
            color="neutral"
            variant="soft"
            icon="i-lucide-arrow-left"
            aria-label="Torna alle card"
            @click="session.goToPhase('cards')"
          />
          <UButton
            size="xl"
            block
            trailing-icon="i-lucide-arrow-right"
            label="Verifica con le flashcard"
            @click="session.goToPhase('flashcards')"
          />
        </div>
      </div>

      <SessionFlashcardDeck
        v-else-if="phase === 'flashcards'"
        :flashcards="chapter.flashcards"
        :results="flashResults"
        @answer="session.recordFlashcard"
        @finished="session.complete"
      />

      <SessionComplete
        v-else
        :book-id="bookId"
        :chapter="chapter"
        :next="next"
        :results="flashResults"
      />
    </main>
  </div>
</template>
