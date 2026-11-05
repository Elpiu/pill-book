<script setup lang="ts">
import type { Card } from '~/types/bookpack'
import type { FlashResult } from '~/utils/progress'

const props = defineProps<{
  cards: Card[]
  startIndex: number
  results: Record<string, FlashResult>
}>()

const emit = defineEmits<{
  change: [index: number]
  finished: []
  answer: [id: string, known: boolean]
}>()

// Una slide in più in coda: raggiungerla con swipe o tap chiude il deck
const slides = computed<(Card | null)[]>(() => [...props.cards, null])
const carousel = useTemplateRef('carousel')
const emblaApi = computed(() => carousel.value?.emblaApi)

function onSelect(index: number) {
  if (index >= props.cards.length) emit('finished')
  else emit('change', index)
}

/**
 * Tap sui bordi: il terzo sinistro torna indietro, il terzo destro va avanti.
 * Dopo un trascinamento Embla blocca il click in fase di cattura, quindi qui arrivano solo i tap.
 */
function onTap(event: MouseEvent) {
  const api = emblaApi.value
  if (!api || window.getSelection()?.toString()) return
  // I pulsanti delle domande non contano come tap sui bordi
  if ((event.target as Element).closest('[data-no-tap]')) return
  const area = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = (event.clientX - area.left) / area.width
  if (position < 1 / 3) api.scrollPrev()
  else if (position > 2 / 3) api.scrollNext()
}

function onAnswer(id: string, known: boolean) {
  emit('answer', id, known)
  emblaApi.value?.scrollNext()
}

function onKeydown(event: KeyboardEvent) {
  // Con il focus dentro il deck le frecce le gestisce già il carosello
  if (event.defaultPrevented) return
  if (event.key === 'ArrowRight') emblaApi.value?.scrollNext()
  else if (event.key === 'ArrowLeft') emblaApi.value?.scrollPrev()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div
    class="h-full"
    data-testid="card-deck"
    @click="onTap"
  >
    <UCarousel
      ref="carousel"
      v-slot="{ item }"
      :items="slides"
      :start-index="startIndex"
      :duration="22"
      align="center"
      :contain-scroll="false"
      :ui="{
        root: 'h-full',
        viewport: 'h-full',
        container: 'h-full ms-0',
        item: 'basis-full ps-4 pe-4 min-h-0 h-full',
      }"
      @select="onSelect"
    >
      <SessionCheckCard
        v-if="item?.type === 'check'"
        :card="item"
        :result="results[item.id]"
        @answer="known => onAnswer(item.id, known)"
      />
      <SessionConceptCard
        v-else-if="item"
        :card="item"
      />
      <div
        v-else
        class="h-full"
      />
    </UCarousel>
  </div>
</template>
