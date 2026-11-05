<script setup lang="ts">
import type { Card } from '~/types/bookpack'

const props = defineProps<{
  cards: Card[]
  startIndex: number
}>()

const emit = defineEmits<{
  change: [index: number]
  finished: []
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
  const area = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = (event.clientX - area.left) / area.width
  if (position < 1 / 3) api.scrollPrev()
  else if (position > 2 / 3) api.scrollNext()
}

function onKeydown(event: KeyboardEvent) {
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
      <SessionConceptCard
        v-if="item"
        :card="item"
      />
      <div
        v-else
        class="h-full"
      />
    </UCarousel>
  </div>
</template>
