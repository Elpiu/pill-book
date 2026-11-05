<script setup lang="ts">
const props = defineProps<{ text: string }>()
const emit = defineEmits<{ back: [], next: [] }>()

const paragraphs = computed(() => props.text.split(/\n\s*\n/).map(part => part.trim()).filter(Boolean))
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="min-h-0 flex-1 overflow-y-auto px-6 pb-4">
      <h2 class="card-title mb-4 font-serif font-semibold text-highlighted">
        Riassunto del capitolo
      </h2>
      <p
        v-for="paragraph in paragraphs"
        :key="paragraph"
        class="card-lead mb-4 font-serif text-default"
      >
        {{ paragraph }}
      </p>
    </div>
    <div class="safe-bottom grid grid-cols-[auto_1fr] gap-3 px-4 pt-3">
      <UButton
        size="xl"
        color="neutral"
        variant="soft"
        icon="i-lucide-arrow-left"
        aria-label="Torna alle card"
        @click="emit('back')"
      />
      <UButton
        size="xl"
        block
        trailing-icon="i-lucide-arrow-right"
        label="Continua con la mindmap"
        @click="emit('next')"
      />
    </div>
  </div>
</template>
