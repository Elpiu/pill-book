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
  procedure: {
    label: 'Come si fa',
    icon: 'i-lucide-list-ordered',
    tint: 'bg-sky-50 dark:bg-sky-950/40',
    accent: 'text-sky-700 dark:text-sky-300',
  },
  check: {
    label: 'Domanda',
    icon: 'i-lucide-circle-help',
    tint: 'bg-violet-50 dark:bg-violet-950/40',
    accent: 'text-violet-700 dark:text-violet-300',
  },
  section: {
    label: 'Nuova parte',
    icon: 'i-lucide-bookmark',
    tint: 'bg-elevated',
    accent: 'text-muted',
  },
  takeaway: {
    label: 'Da portare via',
    icon: 'i-lucide-flag',
    tint: 'bg-emerald-100 dark:bg-emerald-900/40',
    accent: 'text-emerald-800 dark:text-emerald-300',
  },
}

const style = computed(() => STYLES[props.card.type])
const isDense = computed(() => Boolean(props.card.details || props.card.steps?.length || props.card.code))
</script>

<template>
  <article
    class="flex h-full flex-col rounded-2xl px-5 pt-5 pb-3"
    :class="style.tint"
  >
    <p
      class="flex shrink-0 items-center gap-2 pb-2 text-sm font-semibold"
      :class="style.accent"
    >
      <UIcon
        :name="style.icon"
        class="size-5"
        aria-hidden="true"
      />
      {{ style.label }}
    </p>

    <div
      class="card-scroll flex min-h-0 flex-1 flex-col overflow-y-auto"
      data-testid="card-scroll"
    >
      <div class="my-auto py-2">
        <h2
          v-if="card.title"
          class="mb-2 font-serif font-semibold text-highlighted"
          :class="isDense ? 'card-title-dense' : 'card-title'"
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
          class="font-serif text-highlighted"
          :class="isDense ? 'card-lead' : 'card-body'"
        >
          {{ card.body }}
        </p>
        <p
          v-if="card.details"
          class="card-details mt-3 font-serif text-toned"
        >
          {{ card.details }}
        </p>
        <ol
          v-if="card.steps?.length"
          class="card-details mt-3 list-decimal space-y-2 pl-5 font-serif text-toned"
        >
          <li
            v-for="step in card.steps"
            :key="step"
          >
            {{ step }}
          </li>
        </ol>
        <pre
          v-if="card.code"
          class="card-code mt-3 rounded-lg bg-inverted/90 p-3 font-mono break-words whitespace-pre-wrap text-inverted"
        >{{ card.code }}</pre>
        <p
          v-if="card.type === 'section'"
          class="mt-4 text-sm text-muted"
        >
          Un buon punto per fermarsi: riprenderai da qui.
        </p>
      </div>
    </div>

    <p
      v-if="card.page"
      class="shrink-0 pt-1 text-right text-xs text-muted"
    >
      p. {{ card.page }}
    </p>
  </article>
</template>
