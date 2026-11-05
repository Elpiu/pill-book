<script setup lang="ts">
import type { Chapter } from '~/types/bookpack'
import { chapterState, chapterStatusLabel, type ProgressRecord } from '~/utils/progress'

const props = defineProps<{
  bookId: string
  chapter: Chapter
  progress?: ProgressRecord
  suggested: boolean
  last: boolean
}>()

const state = computed(() => chapterState(props.chapter, props.progress))
const label = computed(() => chapterStatusLabel(props.chapter, props.progress))
</script>

<template>
  <li class="relative flex gap-3">
    <div class="flex flex-col items-center">
      <span
        class="z-1 flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold"
        :class="{
          'border-primary bg-primary text-inverted': state === 'done',
          'border-primary bg-default text-primary': state !== 'done' && (suggested || state === 'doing'),
          'border-default bg-default text-muted': state === 'todo' && !suggested,
        }"
      >
        <UIcon
          v-if="state === 'done'"
          name="i-lucide-check"
          class="size-4"
          aria-hidden="true"
        />
        <template v-else>{{ chapter.index }}</template>
      </span>
      <span
        v-if="!last"
        class="w-px flex-1 bg-(--ui-border)"
        :class="{ 'bg-primary': state === 'done' }"
      />
    </div>

    <NuxtLink
      :to="`/book/${bookId}/ch/${chapter.id}`"
      class="mb-3 block min-w-0 flex-1 rounded-xl p-3 transition focus-visible:outline-2 focus-visible:outline-primary"
      :class="suggested
        ? 'bg-primary/10 ring-1 ring-primary/40'
        : 'hover:bg-elevated'"
    >
      <h3 class="font-serif text-lg leading-snug font-semibold">
        {{ chapter.title }}
      </h3>
      <p class="mt-1 text-sm text-muted">
        {{ chapter.tldr }}
      </p>
      <p class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
        <span :class="{ 'font-medium text-primary': state === 'doing' }">{{ label }}</span>
        <span>{{ chapter.estMinutes }} min</span>
      </p>
      <p
        v-if="suggested"
        class="mt-2 flex items-center gap-1 text-sm font-semibold text-primary"
      >
        {{ state === 'doing' ? 'Continua' : 'Inizia da qui' }}
        <UIcon
          name="i-lucide-arrow-right"
          class="size-4"
          aria-hidden="true"
        />
      </p>
    </NuxtLink>
  </li>
</template>
