<script setup lang="ts">
import type { Card, CardType } from '~/types/bookpack'

const props = defineProps<{ card: Card }>()

const STYLES: Record<CardType, { label: string, icon: string, tint: string, accent: string }> = {
  concept: {
    label: 'Concetto',
    icon: 'i-lucide-lightbulb',
    tint: 'bg-teal-50 dark:bg-teal-950/40',
    accent: 'text-teal-700 dark:text-teal-300',
  },
  definition: {
    label: 'Definizione',
    icon: 'i-lucide-book-open-text',
    tint: 'bg-indigo-50 dark:bg-indigo-950/40',
    accent: 'text-indigo-700 dark:text-indigo-300',
  },
  example: {
    label: 'Esempio',
    icon: 'i-lucide-target',
    tint: 'bg-amber-50 dark:bg-amber-950/30',
    accent: 'text-amber-800 dark:text-amber-300',
  },
  quote: {
    label: 'Citazione',
    icon: 'i-lucide-quote',
    tint: 'bg-rose-50 dark:bg-rose-950/30',
    accent: 'text-rose-700 dark:text-rose-300',
  },
  takeaway: {
    label: 'Da portare via',
    icon: 'i-lucide-flag',
    tint: 'bg-emerald-100 dark:bg-emerald-900/40',
    accent: 'text-emerald-800 dark:text-emerald-300',
  },
}

const style = computed(() => STYLES[props.card.type])
</script>

<template>
  <article
    class="flex h-full flex-col overflow-y-auto rounded-2xl p-6"
    :class="style.tint"
  >
    <p
      class="flex items-center gap-2 text-sm font-semibold"
      :class="style.accent"
    >
      <UIcon
        :name="style.icon"
        class="size-5"
        aria-hidden="true"
      />
      {{ style.label }}
    </p>

    <div class="my-auto py-6">
      <h2
        v-if="card.title"
        class="card-title mb-4 font-serif font-semibold text-highlighted"
      >
        {{ card.title }}
      </h2>
      <blockquote
        v-if="card.type === 'quote'"
        class="card-quote font-serif text-highlighted italic"
      >
        “{{ card.body }}”
      </blockquote>
      <p
        v-else
        class="card-body font-serif text-default"
      >
        {{ card.body }}
      </p>
    </div>

    <p
      v-if="card.page"
      class="text-right text-xs text-muted"
    >
      p. {{ card.page }}
    </p>
  </article>
</template>
