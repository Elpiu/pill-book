<script setup lang="ts">
import type { Chapter } from '~/types/bookpack'
import type { FlashResult } from '~/utils/progress'

const props = defineProps<{
  bookId: string
  chapter: Chapter
  next?: Chapter
  results: Record<string, FlashResult>
}>()

const known = computed(() => props.chapter.flashcards.filter(card => props.results[card.id]?.known))
const toReview = computed(() => props.chapter.flashcards.filter(card => props.results[card.id]?.known === false))
const takeaway = computed(() => props.chapter.cards.at(-1)?.body)
</script>

<template>
  <div class="mx-auto flex h-full max-w-xl flex-col overflow-y-auto px-6">
    <div class="my-auto py-6 text-center">
      <span class="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-primary/15 text-primary">
        <UIcon
          name="i-lucide-check"
          class="size-8"
          aria-hidden="true"
        />
      </span>
      <h2 class="font-serif text-2xl font-semibold">
        Capitolo completato
      </h2>
      <p class="mt-1 text-muted">
        {{ chapter.title }}
      </p>
      <p class="mt-4 font-serif text-lg leading-relaxed">
        {{ takeaway }}
      </p>
      <p
        v-if="known.length + toReview.length"
        class="mt-4 text-sm text-muted"
      >
        Sapevi {{ known.length }} flashcard su {{ chapter.flashcards.length }}.
        Le domande torneranno nel ripasso nei prossimi giorni.
      </p>

      <div
        v-if="toReview.length"
        class="mt-4 rounded-xl bg-elevated p-4 text-left"
      >
        <h3 class="mb-2 text-sm font-semibold">
          Da ripassare
        </h3>
        <dl class="space-y-3 text-sm">
          <div
            v-for="card in toReview"
            :key="card.id"
          >
            <dt class="font-medium">
              {{ card.q }}
            </dt>
            <dd class="text-muted">
              {{ card.a }}
            </dd>
          </div>
        </dl>
      </div>
    </div>

    <div class="safe-bottom space-y-2 pt-2">
      <UButton
        v-if="next"
        :to="`/book/${bookId}/ch/${next.id}`"
        size="xl"
        block
        trailing-icon="i-lucide-arrow-right"
        :label="`Prossimo: ${next.title}`"
        :ui="{ label: 'truncate' }"
      />
      <UButton
        :to="`/book/${bookId}`"
        size="xl"
        block
        color="neutral"
        :variant="next ? 'ghost' : 'solid'"
        label="Torna al percorso"
      />
    </div>
  </div>
</template>
