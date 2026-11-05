<script setup lang="ts">
import type { Markmap } from 'markmap-view'

const props = withDefaults(defineProps<{
  markdown: string
  expandLevel?: number
}>(), { expandLevel: 3 })
const emit = defineEmits<{ nodeTap: [text: string] }>()

const svg = useTemplateRef<SVGSVGElement>('svg')
const failed = ref(false)
let map: Markmap | undefined
let resizeObserver: ResizeObserver | undefined

onMounted(async () => {
  try {
    // Le librerie della mindmap sono pesanti e servono solo qui
    const [{ Transformer }, { Markmap: MarkmapView }] = await Promise.all([
      import('markmap-lib'),
      import('markmap-view'),
    ])
    if (!svg.value) return
    const { root } = new Transformer([]).transform(props.markdown)
    map = MarkmapView.create(svg.value, {
      initialExpandLevel: props.expandLevel,
      autoFit: true,
      duration: 250,
      // Etichette a capo e rami stretti: su telefono il testo resta leggibile anche adattato
      maxWidth: 130,
      fitRatio: 0.94,
      paddingX: 6,
      spacingVertical: 10,
      spacingHorizontal: 22,
    }, root)
    resizeObserver = new ResizeObserver(() => map?.fit())
    resizeObserver.observe(svg.value)
  }
  catch (cause) {
    console.error('Mindmap non disponibile', cause)
    failed.value = true
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.destroy()
})

function onClick(event: MouseEvent) {
  const target = event.target as Element
  // Il cerchio comprime il ramo: lo gestisce markmap
  if (target.closest('circle')) return
  const text = target.closest('g.markmap-node')?.querySelector('foreignObject')?.textContent
  if (text) emit('nodeTap', text.trim())
}
</script>

<template>
  <div class="mindmap size-full">
    <p
      v-if="failed"
      class="p-6 text-center text-muted"
    >
      Non è stato possibile disegnare la mindmap.
    </p>
    <svg
      v-else
      ref="svg"
      class="markmap"
      role="img"
      aria-label="Mappa mentale. Tocca i cerchi per aprire o chiudere i rami, pizzica per ingrandire."
      @click="onClick"
    />
  </div>
</template>
