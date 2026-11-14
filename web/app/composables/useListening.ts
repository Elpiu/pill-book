import { computed, ref } from 'vue'
import type { Card } from '~/types/bookpack'
import { ANSWER_TAG, cardScript, summaryScript } from '~/utils/listening'
import type { useSpeech } from './useSpeech'

/**
 * Regia della modalità ascolto: legge le card di un capitolo una dopo l'altra, poi il riassunto.
 * Non tocca né la pagina né il database: chiede alla sessione di spostarsi con le callback, così
 * si prova con un sintetizzatore finto.
 */

export type ListeningPart = 'cards' | 'summary'

export interface ListeningOptions {
  speech: ReturnType<typeof useSpeech>
  cards: () => Card[]
  summary: () => string
  lang: () => string
  voiceURI?: () => string | undefined
  /** La regia è passata a questa card: la sessione la mostra. */
  onCard: (index: number) => void
  onSummary: () => void
  /** Riassunto letto fino in fondo, oppure Avanti durante il riassunto. */
  onFinished: () => void
}

export function useListening(options: ListeningOptions) {
  const { speech } = options
  const active = ref(false)
  const part = ref<ListeningPart>('cards')
  /** Card in lettura; durante il riassunto vale il numero delle card. */
  const index = ref(0)
  // Ogni avvio ha il suo numero: una lettura sostituita non deve far avanzare nulla
  let runs = 0

  /** La card di cui la voce sta leggendo la risposta: va mostrata anche sullo schermo. */
  const revealedCardId = computed(() =>
    active.value && part.value === 'cards' && speech.current.value?.tag === ANSWER_TAG
      ? options.cards()[index.value]?.id
      : undefined,
  )
  const listeningCardId = computed(() =>
    active.value && part.value === 'cards' ? options.cards()[index.value]?.id : undefined,
  )

  function settings() {
    return { lang: options.lang(), voiceURI: options.voiceURI?.() }
  }

  async function run(from: number) {
    const token = ++runs
    active.value = true
    const cards = options.cards()
    for (let i = from; i < cards.length; i++) {
      part.value = 'cards'
      index.value = i
      options.onCard(i)
      const result = await speech.play(cardScript(cards[i]!, options.lang()), settings())
      if (token !== runs || result !== 'done') return
    }
    part.value = 'summary'
    index.value = cards.length
    options.onSummary()
    const result = await speech.play(summaryScript(options.summary(), options.lang()), settings())
    if (token !== runs || result !== 'done') return
    finish()
  }

  function finish() {
    runs++
    active.value = false
    speech.stop()
    options.onFinished()
  }

  /** Avvia dalla card indicata; il numero delle card avvia dal riassunto. */
  function start(from: number) {
    void run(Math.max(0, Math.min(from, options.cards().length)))
  }

  /** Avanti e indietro dalla barra: da una card al riassunto, e oltre il riassunto alla fine. */
  function moveTo(target: number) {
    if (!active.value) return
    const total = options.cards().length
    if (target > total) finish()
    else start(target)
  }

  /** Swipe, tap o frecce dell'utente: la voce riparte dalla card raggiunta. */
  function userMoved(target: number) {
    if (!active.value || (part.value === 'cards' && target === index.value)) return
    start(target)
  }

  function toggle() {
    if (speech.status.value === 'paused') speech.resume()
    else speech.pause()
  }

  function close() {
    runs++
    active.value = false
    speech.stop()
  }

  return {
    active,
    part,
    index,
    revealedCardId,
    listeningCardId,
    start,
    prev: () => moveTo(index.value - 1),
    next: () => moveTo(index.value + 1),
    userMoved,
    toggle,
    skipWait: () => speech.skip(),
    close,
  }
}
