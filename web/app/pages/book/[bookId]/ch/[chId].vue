<script setup lang="ts">
import { chapterAfter, sectionPosition, sessionPhases, type Phase } from '~/utils/progress'

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
    case 'cards': {
      const part = sectionPosition(chapter.value, cardIndex.value)
      const card = `Card ${cardIndex.value + 1} di ${chapter.value.cards.length}`
      return part ? `${card} · Parte ${part.current} di ${part.total}` : card
    }
    case 'summary': return 'Riassunto'
    case 'mindmap': return 'Mindmap'
    case 'flashcards': return 'Flashcard'
    default: return 'Completato'
  }
})

function neighbourPhase(step: 1 | -1): Phase | undefined {
  if (!chapter.value) return undefined
  const phases = sessionPhases(chapter.value)
  return phases[phases.indexOf(phase.value) + step]
}

function move(step: 1 | -1) {
  const target = neighbourPhase(step)
  if (target) session.goToPhase(target)
}

/** Le card e le flashcard gestiscono le frecce da sole. */
function onPhaseKey(event: KeyboardEvent) {
  // Un evento già gestito dal deck non deve far avanzare anche la fase appena aperta
  if (event.defaultPrevented) return
  if (phase.value !== 'mindmap' && phase.value !== 'summary') return
  if (event.key === 'ArrowRight') move(1)
  else if (event.key === 'ArrowLeft') move(-1)
}

onMounted(() => window.addEventListener('keydown', onPhaseKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onPhaseKey))

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
        :results="flashResults"
        @change="session.setCard"
        @finished="move(1)"
        @answer="session.recordFlashcard"
      />

      <SessionSummaryView
        v-else-if="phase === 'summary'"
        :text="chapter.summary"
        @back="move(-1)"
        @next="move(1)"
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
            aria-label="Torna indietro"
            @click="move(-1)"
          />
          <UButton
            size="xl"
            block
            trailing-icon="i-lucide-arrow-right"
            label="Verifica con le flashcard"
            @click="move(1)"
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
