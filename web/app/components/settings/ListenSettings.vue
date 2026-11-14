<script setup lang="ts">
import type { BookPack } from '~/types/bookpack'
import { LISTEN_RATES } from '~/composables/useListenSettings'
import { languageName, splitSentences, voiceKey } from '~/utils/speech'

const props = defineProps<{ packs: BookPack[] }>()

// Reka non ammette valori vuoti nelle select: "auto" è la scelta automatica
const AUTO = 'auto'

const speech = useSpeech()
const listen = useListenSettings()

onMounted(() => {
  speech.loadVoices().catch(() => undefined)
})

/** Una riga per ogni lingua dei libri presenti, con una frase del libro per la prova. */
const languages = computed(() => {
  const found = new Map<string, string>()
  for (const pack of props.packs) {
    const key = voiceKey(pack.book.lang)
    if (found.has(key)) continue
    const card = pack.chapters.flatMap(chapter => chapter.cards).find(item => item.type !== 'section')
    found.set(key, splitSentences(card?.body ?? pack.book.title, key)[0] ?? pack.book.title)
  }
  return [...found].map(([lang, sample]) => ({ lang, sample, name: languageName(lang) }))
})

function voiceItems(lang: string) {
  const automatic = speech.voiceFor(lang)
  return [
    { label: automatic ? `Automatica (${automatic.name})` : 'Automatica', value: AUTO },
    ...speech.voicesFor(lang).map(voice => ({
      label: voice.localService ? voice.name : `${voice.name} · serve la rete`,
      value: voice.voiceURI,
    })),
  ]
}

/** Una voce salvata che non c'è più si mostra come automatica: la lettura fa già così. */
function selectedVoice(lang: string): string {
  const saved = listen.voiceFor(lang)
  return saved && speech.voicesFor(lang).some(voice => voice.voiceURI === saved) ? saved : AUTO
}

function chooseVoice(lang: string, value: string) {
  listen.setVoice(lang, value === AUTO ? undefined : value).catch((cause) => {
    console.error('Voce non salvata', cause)
  })
}

function chooseRate(value: string) {
  listen.setRate(Number(value)).catch((cause) => {
    console.error('Velocità non salvata', cause)
  })
}

function rateLabel(rate: number) {
  return `${String(rate).replace('.', ',')}×`
}

function tryVoice(lang: string, sample: string) {
  speech.rate.value = listen.rate.value
  speech.play([{ kind: 'say', text: sample }], { lang, voiceURI: listen.voiceFor(lang) }).catch(() => undefined)
}
</script>

<template>
  <section
    v-if="speech.supported"
    class="space-y-4"
    data-testid="listen-settings"
  >
    <h2 class="font-semibold">
      Ascolto
    </h2>

    <USwitch
      :model-value="listen.showButton.value"
      label="Mostra il pulsante Ascolta"
      description="Le cuffie nella sessione leggono le card ad alta voce. Spegnilo se preferisci solo leggere."
      @update:model-value="listen.setShowButton($event)"
    />

    <div class="space-y-2">
      <p class="text-sm font-medium">
        Velocità
      </p>
      <UTabs
        :model-value="String(listen.rate.value)"
        :items="LISTEN_RATES.map(rate => ({ label: rateLabel(rate), value: String(rate) }))"
        :content="false"
        size="sm"
        class="w-full"
        @update:model-value="chooseRate(String($event))"
      />
    </div>

    <div
      v-for="language in languages"
      :key="language.lang"
      class="space-y-2"
    >
      <p class="text-sm font-medium">
        Voce per i libri in {{ language.name }}
      </p>
      <p
        v-if="speech.voicesLoaded.value && !speech.voices.value.length"
        class="text-sm text-muted"
      >
        Il browser non elenca le sue voci: si usa quella di sistema.
      </p>
      <p
        v-else-if="speech.voicesLoaded.value && !speech.voicesFor(language.lang).length"
        class="text-sm text-muted"
      >
        Nessuna voce in {{ language.name }} su questo dispositivo.
      </p>
      <div
        v-else
        class="flex gap-2"
      >
        <USelect
          :model-value="selectedVoice(language.lang)"
          :items="voiceItems(language.lang)"
          :aria-label="`Voce per i libri in ${language.name}`"
          class="min-w-0 flex-1"
          @update:model-value="chooseVoice(language.lang, String($event))"
        />
        <UButton
          icon="i-lucide-volume-2"
          color="neutral"
          variant="subtle"
          label="Prova"
          :aria-label="`Prova la voce per i libri in ${language.name}`"
          @click="tryVoice(language.lang, language.sample)"
        />
      </div>
    </div>

    <p class="text-sm text-muted">
      Le voci migliori spesso vanno scaricate dal sistema. Su iPhone: Impostazioni, Accessibilità, Contenuto letto ad alta voce, Voci, poi scegli la lingua e una voce "Migliorata" o "Premium". Su Android: Impostazioni, Accessibilità o Sistema, Output sintesi vocale, poi installa i dati vocali della lingua dal motore di sintesi di Google.
    </p>
  </section>
</template>
