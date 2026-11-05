<script setup lang="ts">
import { it } from '@nuxt/ui/locale'
</script>

<template>
  <UApp :locale="it">
    <NuxtPwaManifest />
    <NuxtPage />
  </UApp>
</template>
