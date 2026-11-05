<script setup lang="ts">
defineProps<{ message: string }>()
</script>

<template>
  <div class="flex min-h-dvh items-center justify-center p-6">
    <UEmpty
      icon="i-lucide-book-x"
      :title="message"
      description="Potrebbe essere stato eliminato da questo dispositivo."
      :actions="[{ label: 'Torna alla libreria', to: '/', icon: 'i-lucide-library' }]"
    />
  </div>
</template>
