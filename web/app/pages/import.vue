<script setup lang="ts">
import { totalMinutes } from '~/utils/validatePack'

const route = useRoute()
const { pack, errors, loading, alreadyImported, fromFile, fromUrl, save, clear } = useImport()

const tabs = [
  { label: 'Da file', value: 'file', icon: 'i-lucide-file-json' },
  { label: 'Da URL', value: 'url', icon: 'i-lucide-link' },
]
const queryUrl = typeof route.query.url === 'string' ? route.query.url : ''
const source = ref(queryUrl ? 'url' : 'file')
const file = ref<File | null>(null)
const url = ref(queryUrl)
const saving = ref(false)
const saveError = ref('')

watch(file, (selected) => {
  if (selected) fromFile(selected)
  else clear()
})
watch(source, clear)

function loadUrl() {
  if (url.value.trim()) fromUrl(url.value.trim())
}

if (queryUrl) loadUrl()

async function confirm() {
  saving.value = true
  saveError.value = ''
  try {
    const bookId = await save()
    if (bookId) await navigateTo(`/book/${bookId}`)
  }
  catch {
    saveError.value = 'Salvataggio non riuscito: lo spazio del browser potrebbe essere esaurito.'
  }
  finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="mx-auto min-h-dvh max-w-2xl pb-10">
    <CommonAppHeader
      title="Importa un libro"
      back="/"
    />

    <main class="space-y-5 px-4 pt-2">
      <UTabs
        v-model="source"
        :items="tabs"
        :content="false"
        class="w-full"
      />

      <UFileUpload
        v-if="source === 'file'"
        v-model="file"
        accept=".json,application/json"
        label="Scegli o trascina un file"
        description="*.bookpack.json"
        icon="i-lucide-upload"
        layout="list"
        class="min-h-44 w-full"
      />

      <form
        v-else
        class="flex gap-2"
        @submit.prevent="loadUrl"
      >
        <UInput
          v-model="url"
          type="url"
          placeholder="https://…/libro.bookpack.json"
          size="xl"
          class="min-w-0 flex-1"
          aria-label="Indirizzo del pack"
        />
        <UButton
          type="submit"
          size="xl"
          label="Carica"
          :loading="loading"
        />
      </form>

      <p
        v-if="loading && source === 'file'"
        class="text-center text-muted"
      >
        Controllo il file…
      </p>

      <UAlert
        v-if="errors.length"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
        title="Questo pack non si può importare"
      >
        <template #description>
          <ul class="mt-1 list-disc space-y-1 pl-4">
            <li
              v-for="message in errors"
              :key="message"
            >
              {{ message }}
            </li>
          </ul>
        </template>
      </UAlert>

      <section
        v-if="pack"
        class="space-y-4 rounded-2xl border border-default bg-elevated/40 p-4"
        aria-label="Anteprima"
      >
        <div class="flex gap-4">
          <BookCover
            :color="pack.book.coverColor"
            :title="pack.book.title"
            class="h-24 w-16 shrink-0"
          />
          <div class="min-w-0">
            <h2 class="font-serif text-xl leading-snug font-semibold">
              {{ pack.book.title }}
            </h2>
            <p
              v-if="pack.book.author"
              class="text-sm text-muted"
            >
              {{ pack.book.author }}
            </p>
            <p class="mt-2 text-sm">
              {{ pack.chapters.length }} capitoli · {{ totalMinutes(pack) }} minuti in totale
            </p>
          </div>
        </div>

        <UAlert
          v-if="alreadyImported"
          color="warning"
          variant="subtle"
          icon="i-lucide-refresh-cw"
          title="Questo libro è già nella tua libreria"
          description="Puoi aggiornarlo: il progresso resta. Quello di capitoli o card che non esistono più viene ignorato."
        />
        <UAlert
          v-if="saveError"
          color="error"
          variant="subtle"
          :title="saveError"
        />

        <UButton
          size="xl"
          block
          :loading="saving"
          :label="alreadyImported ? 'Aggiorna mantenendo il progresso' : 'Aggiungi alla libreria'"
          @click="confirm"
        />
      </section>
    </main>
  </div>
</template>
