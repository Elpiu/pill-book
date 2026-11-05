<script setup lang="ts">
import type { FlashResult } from '~/utils/progress'

export interface DeckCard {
  id: string
  q: string
  a: string
  page?: number | null
  context?: string  // da dove viene: serve nel ripasso, dove i libri si mescolano
}

const props = defineProps<{
  flashcards: DeckCard[]
  results: Record<string, FlashResult>
}>()

const emit = defineEmits<{
  answer: [id: string, known: boolean]
  finished: []
}>()

// Si riprende dalla prima flashcard senza esito
const index = ref(Math.max(props.flashcards.findIndex(card => !props.results[card.id]), 0))
const flipped = ref(false)
const current = computed(() => props.flashcards[index.value]!)

function answer(known: boolean) {
  emit('answer', current.value.id, known)
  flipped.value = false
  if (index.value + 1 >= props.flashcards.length) emit('finished')
  else index.value += 1
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault()
    flipped.value = !flipped.value
  }
  else if (flipped.value && event.key === 'ArrowRight') {
    answer(true)
  }
  else if (flipped.value && event.key === 'ArrowLeft') {
    answer(false)
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="flex h-full flex-col px-4">
    <p class="pb-3 text-center text-sm text-muted">
      Flashcard {{ index + 1 }} di {{ flashcards.length }}
      <span
        v-if="current.context"
        class="mt-0.5 block truncate text-xs"
      >{{ current.context }}</span>
    </p>

    <button
      :key="current.id"
      type="button"
      class="flip-scene min-h-0 flex-1 text-left"
      :aria-label="flipped ? 'Torna alla domanda' : 'Mostra la risposta'"
      @click="flipped = !flipped"
    >
      <div
        class="flip-card relative size-full"
        :class="{ 'is-flipped': flipped }"
      >
        <div class="flip-face absolute inset-0 flex flex-col overflow-y-auto rounded-2xl bg-elevated p-6">
          <p class="text-sm font-semibold text-primary">
            Domanda
          </p>
          <p class="card-title my-auto py-4 font-serif font-semibold text-highlighted">
            {{ current.q }}
          </p>
          <p class="text-center text-sm text-muted">
            Tocca per vedere la risposta
          </p>
        </div>
        <div class="flip-face flip-back absolute inset-0 flex flex-col overflow-y-auto rounded-2xl bg-primary/10 p-6">
          <p class="text-sm font-semibold text-primary">
            Risposta
          </p>
          <p class="card-body my-auto py-4 font-serif text-highlighted">
            {{ current.a }}
          </p>
          <p
            v-if="current.page"
            class="text-right text-xs text-muted"
          >
            p. {{ current.page }}
          </p>
        </div>
      </div>
    </button>

    <div
      class="safe-bottom grid grid-cols-2 gap-3 pt-4 transition-opacity"
      :class="flipped ? 'opacity-100' : 'pointer-events-none opacity-0'"
      :inert="!flipped"
    >
      <UButton
        size="xl"
        color="neutral"
        variant="soft"
        block
        icon="i-lucide-rotate-ccw"
        label="Da ripassare"
        @click="answer(false)"
      />
      <UButton
        size="xl"
        block
        icon="i-lucide-check"
        label="Lo sapevo"
        @click="answer(true)"
      />
    </div>
  </div>
</template>
