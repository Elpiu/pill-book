<script setup lang="ts">
import type { Overview } from '~/types/bookpack'

defineProps<{ overview: Overview }>()
const open = ref(false)
</script>

<template>
  <UCollapsible
    v-model:open="open"
    class="rounded-xl border border-default bg-elevated/40"
  >
    <button
      type="button"
      class="flex w-full items-center justify-between gap-2 px-4 py-3 text-left font-medium"
    >
      Di cosa parla
      <UIcon
        name="i-lucide-chevron-down"
        class="size-5 transition-transform"
        :class="{ 'rotate-180': open }"
      />
    </button>
    <template #content>
      <div class="space-y-4 px-4 pb-4">
        <p class="font-serif leading-relaxed">
          {{ overview.summary }}
        </p>
        <div>
          <h3 class="mb-2 text-sm font-semibold text-muted">
            Idee portanti
          </h3>
          <ul class="space-y-2">
            <li
              v-for="idea in overview.keyIdeas"
              :key="idea"
              class="flex gap-2"
            >
              <UIcon
                name="i-lucide-sparkle"
                class="mt-1 size-4 shrink-0 text-primary"
              />
              <span>{{ idea }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </UCollapsible>
</template>
