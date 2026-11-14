<script setup lang="ts">
import { LISTEN_RATES } from '~/composables/useListenSettings'
import { chapterAfter, sectionPosition, sessionPhases, type Phase } from '~/utils/progress'
import { languageName, voiceAvailability } from '~/utils/speech'

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

// --- Modalità ascolto ----------------------------------------------------------------------------

const toast = useToast()
const listenSettings = useListenSettings()
const speech = useSpeech()
const deck = useTemplateRef('deck')
const bookLang = computed(() => pack.value?.book.lang ?? 'it')
// La regia cambia fase da sola: quei cambi non devono chiudere l'ascolto, quelli dell'utente sì
let expectedPhase: Phase | undefined

function phaseByListening(target: Phase) {
  // Una fase già attiva non scatena il watch: il marcatore resterebbe appeso
  if (phase.value === target) return
  expectedPhase = target
  session.goToPhase(target)
}

const listening = useListening({
  speech,
  cards: () => chapter.value?.cards ?? [],
  summary: () => chapter.value?.summary ?? '',
  lang: () => bookLang.value,
  voiceURI: () => listenSettings.voiceFor(bookLang.value),
  onCard(index) {
    if (phase.value === 'cards') {
      deck.value?.scrollTo(index)
      return
    }
    session.setCard(index)
    phaseByListening('cards')
  },
  onSummary: () => phaseByListening('summary'),
  onFinished() {
    phaseByListening('mindmap')
    toast.add({
      title: 'Fine dell\'ascolto',
      description: 'Continua con mindmap e flashcard.',
      icon: 'i-lucide-headphones',
    })
  },
})

watch(phase, (current) => {
  if (current === expectedPhase) {
    expectedPhase = undefined
    return
  }
  listening.close()
})

const availability = computed(() => voiceAvailability(speech.voices.value, bookLang.value))
const showListen = computed(() =>
  speech.supported && listenSettings.showButton.value && (phase.value === 'cards' || phase.value === 'summary'),
)
const listenLabel = computed(() => {
  if (listening.active.value) return 'Chiudi l\'ascolto'
  if (availability.value === 'missing') return `Ascolto non disponibile: nessuna voce in ${languageName(bookLang.value)}`
  return 'Ascolta il capitolo'
})
const listenWhere = computed(() =>
  listening.part.value === 'summary'
    ? 'Riassunto'
    : `Card ${listening.index.value + 1} di ${chapter.value?.cards.length ?? 0}`,
)

/** Parte solo da questo tocco: su iPhone la voce non può partire senza un gesto. */
function onListenButton() {
  if (listening.active.value) {
    listening.close()
    return
  }
  if (availability.value === 'missing') {
    toast.add({
      title: `Nessuna voce in ${languageName(bookLang.value)} su questo dispositivo`,
      description: 'Puoi aggiungerla dalle impostazioni del telefono.',
      icon: 'i-lucide-circle-alert',
      color: 'warning',
    })
    return
  }
  speech.rate.value = listenSettings.rate.value
  listening.start(phase.value === 'summary' ? (chapter.value?.cards.length ?? 0) : cardIndex.value)
}

function onCardChange(index: number) {
  session.setCard(index)
  listening.userMoved(index)
}

function cycleRate() {
  const current = LISTEN_RATES.indexOf(speech.rate.value)
  const next = LISTEN_RATES[(current + 1) % LISTEN_RATES.length]!
  speech.setRate(next)
  listenSettings.setRate(next).catch((cause) => {
    console.error('Velocità non salvata', cause)
  })
}

/** Con lo schermo bloccato la voce si ferma comunque: meglio una pausa visibile al ritorno. */
function onVisibility() {
  if (document.hidden && listening.active.value) speech.pause()
}

onMounted(() => {
  document.addEventListener('visibilitychange', onVisibility)
  speech.loadVoices().catch(() => undefined)
})
onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', onVisibility)
  listening.close()
})

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
      <UButton
        v-if="showListen"
        icon="i-lucide-headphones"
        :color="listening.active.value ? 'primary' : 'neutral'"
        :variant="listening.active.value ? 'soft' : 'ghost'"
        size="lg"
        :class="{ 'opacity-50': availability === 'missing' && !listening.active.value }"
        :aria-label="listenLabel"
        :aria-pressed="listening.active.value"
        data-testid="listen-button"
        @click="onListenButton"
      />
      <span
        v-else
        class="w-3"
      />
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
        ref="deck"
        :class="{ 'safe-bottom': !listening.active.value }"
        :cards="chapter.cards"
        :start-index="cardIndex"
        :results="flashResults"
        :listening-id="listening.listeningCardId.value"
        :reveal-id="listening.revealedCardId.value"
        @change="onCardChange"
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

    <SessionListenBar
      v-if="listening.active.value"
      :status="speech.status.value"
      :rate="speech.rate.value"
      :wait-remaining="speech.waitRemaining.value"
      :where="listenWhere"
      :error="speech.error.value"
      @prev="listening.prev"
      @toggle="listening.toggle"
      @next="listening.next"
      @rate="cycleRate"
      @skip="listening.skipWait"
      @close="listening.close"
    />
  </div>
</template>
