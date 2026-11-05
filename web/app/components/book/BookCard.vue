<script setup lang="ts">
import type { LibraryItem } from '~/composables/useLibrary'
import { bookPercent } from '~/utils/progress'

const props = defineProps<{ item: LibraryItem }>()

const book = computed(() => props.item.record.pack.book)
const percent = computed(() => bookPercent(props.item.record.pack, props.item.progress))
const lastOpened = computed(() => {
  const date = props.item.progress?.lastOpenedAt
  return date
    ? new Date(date).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
    : undefined
})
</script>

<template>
  <NuxtLink
    :to="`/book/${book.id}`"
    class="flex gap-4 rounded-xl border border-default bg-elevated/40 p-3 transition hover:bg-elevated focus-visible:outline-2 focus-visible:outline-primary"
  >
    <BookCover
      :color="book.coverColor"
      :title="book.title"
      class="h-24 w-16 shrink-0"
    />
    <div class="flex min-w-0 flex-1 flex-col">
      <h2 class="line-clamp-2 font-serif text-lg leading-snug font-semibold">
        {{ book.title }}
      </h2>
      <p
        v-if="book.author"
        class="truncate text-sm text-muted"
      >
        {{ book.author }}
      </p>
      <div class="mt-auto pt-2">
        <UProgress
          :model-value="percent"
          size="sm"
          :aria-label="`Letto al ${percent}%`"
        />
        <p class="mt-1 flex justify-between text-xs text-muted">
          <span>{{ percent }}%</span>
          <span v-if="lastOpened">Aperto il {{ lastOpened }}</span>
        </p>
      </div>
    </div>
  </NuxtLink>
</template>
