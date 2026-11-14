<script setup lang="ts">
import type { SpeechStatus } from '~/composables/useSpeech'

const props = defineProps<{
  status: SpeechStatus
  rate: number
  /** Millisecondi rimasti per pensare a una domanda. */
  waitRemaining: number
  /** Dove si trova la lettura: "Card 3 di 12" o "Riassunto". */
  where: string
  error?: string
}>()

const emit = defineEmits<{
  prev: []
  toggle: []
  next: []
  rate: []
  skip: []
  close: []
}>()

const paused = computed(() => props.status === 'paused')
const seconds = computed(() => Math.ceil(props.waitRemaining / 1000))
const rateLabel = computed(() => `${String(props.rate).replace('.', ',')}×`)
const state = computed(() => {
  if (props.error) return 'La voce si è interrotta: tocca riprendi per riprovare'
  if (paused.value) return `In pausa · ${props.where}`
  if (props.status === 'waiting') return `Pensa alla risposta · ${seconds.value}`
  return props.where
})
</script>

<template>
  <section
    class="safe-bottom border-t border-default bg-default px-3 pt-2"
    aria-label="Controlli dell'ascolto"
    data-testid="listen-bar"
  >
    <div class="flex items-center gap-2 pb-1">
      <UIcon
        name="i-lucide-headphones"
        class="size-4 shrink-0 text-primary"
        aria-hidden="true"
      />
      <p
        class="min-w-0 flex-1 truncate text-xs text-muted"
        role="status"
        aria-live="polite"
        data-testid="listen-state"
      >
        {{ state }}
      </p>
      <UButton
        v-if="status === 'waiting'"
        size="xs"
        color="neutral"
        variant="soft"
        label="Mostra ora"
        aria-label="Salta l'attesa e mostra la risposta"
        @click="emit('skip')"
      />
    </div>
    <div class="flex items-center justify-between gap-1 pb-1">
      <UButton
        size="lg"
        color="neutral"
        variant="ghost"
        :label="rateLabel"
        :aria-label="`Velocità ${rateLabel}: tocca per cambiarla`"
        class="min-w-14 justify-center tabular-nums"
        @click="emit('rate')"
      />
      <div class="flex items-center gap-1">
        <UButton
          size="lg"
          color="neutral"
          variant="ghost"
          icon="i-lucide-skip-back"
          aria-label="Card precedente"
          @click="emit('prev')"
        />
        <UButton
          size="xl"
          :icon="paused ? 'i-lucide-play' : 'i-lucide-pause'"
          :aria-label="paused ? 'Riprendi l\'ascolto' : 'Metti in pausa'"
          @click="emit('toggle')"
        />
        <UButton
          size="lg"
          color="neutral"
          variant="ghost"
          icon="i-lucide-skip-forward"
          aria-label="Card successiva"
          @click="emit('next')"
        />
      </div>
      <UButton
        size="lg"
        color="neutral"
        variant="ghost"
        icon="i-lucide-x"
        aria-label="Chiudi l'ascolto e torna alla lettura"
        class="min-w-14 justify-center"
        @click="emit('close')"
      />
    </div>
  </section>
</template>
