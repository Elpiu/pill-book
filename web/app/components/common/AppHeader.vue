<script setup lang="ts">
defineProps<{
  title: string
  back?: string
}>()
</script>

<template>
  <header class="safe-top sticky top-0 z-10 flex items-center gap-1 bg-default/90 px-2 pb-2 backdrop-blur">
    <UButton
      v-if="back"
      :to="back"
      icon="i-lucide-arrow-left"
      color="neutral"
      variant="ghost"
      size="lg"
      aria-label="Indietro"
    />
    <h1 class="min-w-0 flex-1 truncate px-2 text-lg font-semibold">
      {{ title }}
    </h1>
    <slot />
  </header>
</template>
