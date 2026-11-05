<script setup lang="ts">
import { db, recordReview } from '~/db'
import type { FlashResult } from '~/utils/progress'
import { dueItems, nextDueDate, type ReviewItem } from '~/utils/review'

const items = shallowRef<ReviewItem[]>([])
const results = ref<Record<string, FlashResult>>({})
const status = ref<'loading' | 'reviewing' | 'empty' | 'done'>('loading')
const nextDue = ref<Date>()

/** L'elenco si fissa all'apertura: una domanda sbagliata torna domani, non durante questo giro. */
onMounted(async () => {
  const [books, reviews] = await Promise.all([db.books.toArray(), db.reviews.toArray()])
  const packs = books.map(book => book.pack)
  const now = new Date()
  items.value = dueItems(reviews, packs, now)
  nextDue.value = nextDueDate(reviews, packs, now)
  status.value = items.value.length ? 'reviewing' : 'empty'
})

const known = computed(() => Object.values(results.value).filter(result => result.known).length)

const nextDueLabel = computed(() =>
  nextDue.value?.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' }),
)

function onAnswer(id: string, isKnown: boolean) {
  results.value = { ...results.value, [id]: { known: isKnown, at: new Date().toISOString() } }
  const item = items.value.find(entry => entry.id === id)
  if (!item) return
  recordReview(item.bookId, item.itemId, isKnown).catch((cause) => {
    console.error('Salvataggio del ripasso non riuscito', cause)
  })
}

useHead({ title: 'Ripasso' })
</script>

<template>
  <div class="fixed inset-0 flex flex-col">
    <CommonAppHeader
      title="Ripasso di oggi"
      back="/"
    />

    <main class="min-h-0 flex-1">
      <SessionFlashcardDeck
        v-if="status === 'reviewing'"
        :flashcards="items"
        :results="results"
        @answer="onAnswer"
        @finished="status = 'done'"
      />

      <div
        v-else-if="status === 'empty'"
        class="flex h-full items-center justify-center p-6"
      >
        <UEmpty
          icon="i-lucide-repeat"
          title="Niente da ripassare oggi"
          :description="nextDueLabel
            ? `Le prossime domande tornano ${nextDueLabel}.`
            : 'Le domande a cui rispondi durante la lettura torneranno qui nei giorni successivi.'"
          :actions="[{ label: 'Torna alla libreria', to: '/', icon: 'i-lucide-library' }]"
        />
      </div>

      <div
        v-else-if="status === 'done'"
        class="flex h-full items-center justify-center p-6"
      >
        <UEmpty
          icon="i-lucide-check"
          title="Ripasso finito"
          :description="`Sapevi ${known} domande su ${items.length}. Quelle da ripassare tornano domani, le altre più avanti.`"
          :actions="[{ label: 'Torna alla libreria', to: '/', icon: 'i-lucide-library' }]"
        />
      </div>
    </main>
  </div>
</template>
