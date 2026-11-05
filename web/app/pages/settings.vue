<script setup lang="ts">
import { db, deleteBook, exportProgress, importProgress, resetProgress } from '~/db'
import { parseProgressExport, type ProgressExport } from '~/utils/progress'

const toast = useToast()
const { $pwa } = useNuxtApp()
const { fontScale, theme, restore, setFontScale, setTheme } = useSettings()
const { data: books } = useLiveQuery(() => db.books.toArray())

const themes = [
  { label: 'Sistema', value: 'system', icon: 'i-lucide-monitor' },
  { label: 'Chiaro', value: 'light', icon: 'i-lucide-sun' },
  { label: 'Scuro', value: 'dark', icon: 'i-lucide-moon' },
]

// --- Export e import ---------------------------------------------------------------------------

const fileInput = useTemplateRef<HTMLInputElement>('fileInput')
const pendingImport = shallowRef<ProgressExport>()
const importError = ref('')

async function downloadProgress() {
  const data = await exportProgress()
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `bookpack-progresso-${data.exportedAt.slice(0, 10)}.json`
  link.click()
  URL.revokeObjectURL(link.href)
}

async function onImportFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  importError.value = ''
  try {
    pendingImport.value = parseProgressExport(await file.text())
  }
  catch (cause) {
    importError.value = cause instanceof Error ? cause.message : String(cause)
  }
}

async function applyImport(mode: 'merge' | 'replace') {
  if (!pendingImport.value) return
  await importProgress(pendingImport.value, mode)
  pendingImport.value = undefined
  await restore()
  toast.add({ title: 'Progresso importato', color: 'success', icon: 'i-lucide-check' })
}

// --- Azioni distruttive ------------------------------------------------------------------------

interface Confirmation {
  title: string
  description: string
  action: string
  run: () => Promise<void>
}

const confirmation = shallowRef<Confirmation>()
const confirmOpen = computed({
  get: () => Boolean(confirmation.value),
  set: (open) => {
    if (!open) confirmation.value = undefined
  },
})

async function runConfirmation() {
  await confirmation.value?.run()
  confirmation.value = undefined
}

function askDelete(id: string, title: string) {
  confirmation.value = {
    title: `Eliminare "${title}"?`,
    description: 'Il libro e il suo progresso verranno rimossi da questo dispositivo. Il libro si può reimportare, il progresso no.',
    action: 'Elimina',
    run: () => deleteBook(id),
  }
}

function askReset(id: string, title: string) {
  confirmation.value = {
    title: `Azzerare il progresso di "${title}"?`,
    description: 'Posizioni, esiti delle flashcard e ripassi di questo libro verranno cancellati.',
    action: 'Azzera',
    run: () => resetProgress(id),
  }
}

function askResetAll() {
  confirmation.value = {
    title: 'Azzerare tutto il progresso?',
    description: 'Posizioni, esiti delle flashcard e ripassi di tutti i libri verranno cancellati. Se vuoi conservarli, esportali prima.',
    action: 'Azzera tutto',
    run: () => resetProgress(),
  }
}
</script>

<template>
  <div class="mx-auto min-h-dvh max-w-2xl pb-10">
    <CommonAppHeader
      title="Impostazioni"
      back="/"
    />

    <main class="space-y-8 px-4 pt-2">
      <section
        v-if="!$pwa?.isPWAInstalled"
        class="space-y-3"
      >
        <h2 class="font-semibold">
          Installa l'app
        </h2>
        <UButton
          v-if="$pwa?.showInstallPrompt"
          icon="i-lucide-smartphone"
          label="Installa Bookpack"
          @click="$pwa.install()"
        />
        <p class="text-sm text-muted">
          Così si apre come un'app e funziona offline. Su iPhone: in Safari tocca Condividi, poi Aggiungi alla schermata Home. Su Android: dal menu di Chrome, Installa app o Aggiungi a schermata Home.
        </p>
      </section>

      <section class="space-y-3">
        <h2 class="font-semibold">
          Tema
        </h2>
        <UTabs
          :model-value="theme"
          :items="themes"
          :content="false"
          class="w-full"
          @update:model-value="setTheme($event as 'system' | 'light' | 'dark')"
        />
      </section>

      <section class="space-y-3">
        <h2 class="font-semibold">
          Dimensione del testo delle card
        </h2>
        <UTabs
          :model-value="String(fontScale)"
          :items="FONT_SCALES.map(scale => ({ label: scale.label, value: String(scale.value) }))"
          :content="false"
          size="sm"
          class="w-full"
          @update:model-value="setFontScale(Number($event))"
        />
        <p
          class="rounded-xl bg-elevated p-4 font-serif card-body"
        >
          Il tempo è la materia grezza di tutto.
        </p>
      </section>

      <section class="space-y-3">
        <h2 class="font-semibold">
          Progresso
        </h2>
        <p class="text-sm text-muted">
          Il file contiene posizioni, esiti, ripassi e impostazioni. I libri si reimportano dai loro pack.
        </p>
        <div class="flex flex-wrap gap-2">
          <UButton
            icon="i-lucide-download"
            color="neutral"
            variant="subtle"
            label="Esporta"
            @click="downloadProgress"
          />
          <UButton
            icon="i-lucide-upload"
            color="neutral"
            variant="subtle"
            label="Importa"
            @click="fileInput?.click()"
          />
          <UButton
            icon="i-lucide-eraser"
            color="error"
            variant="subtle"
            label="Azzera tutto"
            @click="askResetAll"
          />
        </div>
        <input
          ref="fileInput"
          type="file"
          accept=".json,application/json"
          class="hidden"
          aria-label="File del progresso da importare"
          @change="onImportFile"
        >
        <UAlert
          v-if="importError"
          color="error"
          variant="subtle"
          :title="importError"
        />
      </section>

      <section
        v-if="books?.length"
        class="space-y-3"
      >
        <h2 class="font-semibold">
          Libri su questo dispositivo
        </h2>
        <ul class="divide-y divide-default rounded-xl border border-default">
          <li
            v-for="book in books"
            :key="book.id"
            class="flex items-center gap-1 p-3"
          >
            <span class="min-w-0 flex-1 truncate font-serif">{{ book.pack.book.title }}</span>
            <UButton
              icon="i-lucide-eraser"
              color="neutral"
              variant="ghost"
              :aria-label="`Azzera il progresso di ${book.pack.book.title}`"
              @click="askReset(book.id, book.pack.book.title)"
            />
            <UButton
              icon="i-lucide-trash-2"
              color="error"
              variant="ghost"
              :aria-label="`Elimina ${book.pack.book.title}`"
              @click="askDelete(book.id, book.pack.book.title)"
            />
          </li>
        </ul>
      </section>
    </main>

    <UModal
      v-model:open="confirmOpen"
      :title="confirmation?.title"
      :description="confirmation?.description"
    >
      <template #footer>
        <div class="flex w-full justify-end gap-2">
          <UButton
            color="neutral"
            variant="ghost"
            label="Annulla"
            @click="confirmation = undefined"
          />
          <UButton
            color="error"
            :label="confirmation?.action"
            @click="runConfirmation"
          />
        </div>
      </template>
    </UModal>

    <UModal
      :open="Boolean(pendingImport)"
      title="Come vuoi importare il progresso?"
      description="Fondendo si tiene il punto più avanzato di ogni capitolo. Sostituendo si cancella quello attuale."
      @update:open="(open: boolean) => { if (!open) pendingImport = undefined }"
    >
      <template #footer>
        <div class="flex w-full justify-end gap-2">
          <UButton
            color="error"
            variant="ghost"
            label="Sostituisci"
            @click="applyImport('replace')"
          />
          <UButton
            label="Fondi"
            @click="applyImport('merge')"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
