<script setup lang="ts">
const { $pwa } = useNuxtApp()
</script>

<template>
  <div
    v-if="$pwa?.showInstallPrompt"
    class="flex items-center gap-2 rounded-2xl border border-default bg-elevated/40 p-3"
  >
    <UIcon
      name="i-lucide-smartphone"
      class="size-5 shrink-0 text-primary"
      aria-hidden="true"
    />
    <p class="min-w-0 flex-1 text-sm">
      Installa Bookpack per aprirlo come un'app e leggere offline.
    </p>
    <UButton
      size="sm"
      label="Installa"
      @click="$pwa.install()"
    />
    <UButton
      size="sm"
      color="neutral"
      variant="ghost"
      icon="i-lucide-x"
      aria-label="Non ora"
      @click="$pwa.cancelInstall()"
    />
  </div>
</template>
