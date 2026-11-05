<script setup lang="ts">
const props = defineProps<{
  color?: string | null
  title: string
}>()

const initial = computed(() => props.title.trim().charAt(0).toUpperCase())
</script>

<template>
  <div
    class="flex items-center justify-center rounded-md font-serif text-3xl font-semibold text-white shadow-sm"
    :style="{ backgroundColor: color ?? '#0f766e', backgroundImage: 'linear-gradient(90deg, rgb(0 0 0 / 0.22) 0 7%, transparent 7%)' }"
    aria-hidden="true"
  >
    {{ initial }}
  </div>
</template>
