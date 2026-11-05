<script setup lang="ts">
import type { Card } from '~/types/bookpack'
import type { FlashResult } from '~/utils/progress'

const props = defineProps<{
  card: Card
  result?: FlashResult
}>()

const emit = defineEmits<{ answer: [known: boolean] }>()

// Una domanda già affrontata mostra subito la risposta: tornandoci si rilegge
const revealed = ref(Boolean(props.result))
</script>

<template>
  <article class="flex h-full flex-col rounded-2xl bg-violet-50 px-5 pt-5 pb-3 dark:bg-violet-950/40">
    <p class="flex shrink-0 items-center gap-2 pb-2 text-sm font-semibold text-violet-700 dark:text-violet-300">
      <UIcon
        name="i-lucide-circle-help"
        class="size-5"
        aria-hidden="true"
      />
      Fermati un momento
    </p>

    <div class="card-scroll flex min-h-0 flex-1 flex-col overflow-y-auto">
      <div class="my-auto py-2">
        <h2 class="card-title-dense font-serif font-semibold text-highlighted">
          {{ card.body }}
        </h2>
        <div
          v-if="revealed"
          class="mt-4"
        >
          <p class="mb-1 text-sm font-semibold text-violet-700 dark:text-violet-300">
            Risposta
          </p>
          <p class="card-lead font-serif text-default">
            {{ card.answer }}
          </p>
        </div>
        <p
          v-else
          class="mt-4 text-sm text-muted"
        >
          Prova a rispondere con parole tue, poi controlla.
        </p>
      </div>
    </div>

    <div
      data-no-tap
      class="shrink-0 pt-1"
    >
      <UButton
        v-if="!revealed"
        block
        size="xl"
        color="neutral"
        variant="soft"
        label="Mostra la risposta"
        @click="revealed = true"
      />
      <div
        v-else
        class="grid grid-cols-2 gap-3"
      >
        <UButton
          block
          size="lg"
          color="neutral"
          :variant="result?.known === false ? 'solid' : 'soft'"
          icon="i-lucide-rotate-ccw"
          label="Da ripassare"
          @click="emit('answer', false)"
        />
        <UButton
          block
          size="lg"
          :variant="result?.known === false ? 'soft' : 'solid'"
          icon="i-lucide-check"
          label="Lo sapevo"
          @click="emit('answer', true)"
        />
      </div>
      <p
        v-if="card.page"
        class="mt-2 text-right text-xs text-muted"
      >
        p. {{ card.page }}
      </p>
    </div>
  </article>
</template>
