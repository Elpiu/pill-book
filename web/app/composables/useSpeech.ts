import { computed, getCurrentScope, onScopeDispose, ref, shallowRef } from 'vue'
import { pickVoice, rankVoices, type SpeechItem, type VoiceInfo } from '~/utils/speech'

/**
 * Sintesi vocale del browser, senza sapere nulla di libri: legge una coda di frasi e pause.
 *
 * Pausa e ripresa ripartono dall'inizio della frase corrente con cancel e un nuovo avvio, perché
 * speechSynthesis.pause() su Android non riprende in modo affidabile.
 */

export type SpeechStatus = 'idle' | 'speaking' | 'waiting' | 'paused'
export type PlayResult = 'done' | 'stopped'

/** La parte di SpeechSynthesis usata qui: si può sostituire nei test. */
export interface SynthLike {
  getVoices(): VoiceInfo[]
  speak(utterance: UtteranceLike): void
  cancel(): void
  addEventListener?(type: 'voiceschanged', listener: () => void): void
  removeEventListener?(type: 'voiceschanged', listener: () => void): void
}

export interface UtteranceLike {
  text: string
  lang: string
  voice: VoiceInfo | null
  rate: number
  onend: (() => void) | null
  onerror: ((event: { error: string }) => void) | null
}

export interface SpeechOptions {
  synth?: SynthLike
  createUtterance?: (text: string) => UtteranceLike
  browserLangs?: readonly string[]
}

/** Alcuni Safari non mandano voiceschanged: si riprova per qualche secondo. */
const VOICE_POLL_MS = 250
const VOICE_POLL_LIMIT_MS = 3000
const COUNTDOWN_TICK_MS = 100
/** Errori che arrivano quando siamo noi a interrompere la frase. */
const OWN_INTERRUPTIONS = new Set(['interrupted', 'canceled'])

function browserSynth(): SynthLike | undefined {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return undefined
  return window.speechSynthesis as unknown as SynthLike
}

export function useSpeech(options: SpeechOptions = {}) {
  const synth = options.synth ?? browserSynth()
  const createUtterance = options.createUtterance
    ?? (text => new SpeechSynthesisUtterance(text) as unknown as UtteranceLike)
  const browserLangs = options.browserLangs
    ?? (typeof navigator === 'undefined' ? [] : navigator.languages ?? [navigator.language])

  const supported = Boolean(synth)
  const voices = shallowRef<VoiceInfo[]>([])
  const voicesLoaded = ref(false)
  const status = ref<SpeechStatus>('idle')
  const rate = ref(1)
  const items = shallowRef<SpeechItem[]>([])
  const position = ref(0)
  const current = computed<SpeechItem | undefined>(() => items.value[position.value])
  /** Millisecondi rimasti di un'attesa da saltare, per il conto alla rovescia. */
  const waitRemaining = ref(0)
  const error = ref<string>()

  let lang = ''
  let voice: VoiceInfo | undefined
  // Ogni avvio ha il suo numero: gli eventi di una frase interrotta non devono far avanzare la coda
  let run = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let ticker: ReturnType<typeof setInterval> | undefined
  // Chrome può liberare una utterance prima della fine e non chiamare onend: si tiene un riferimento
  let _activeUtterance: UtteranceLike | undefined
  let finish: ((result: PlayResult) => void) | undefined

  function readVoices(): boolean {
    const list = synth?.getVoices() ?? []
    if (list.length) voices.value = list
    return list.length > 0
  }

  const onVoicesChanged = () => {
    readVoices()
    voicesLoaded.value = true
  }

  let loading: Promise<void> | undefined
  /** L'elenco può arrivare vuoto e popolarsi dopo; si aspetta al massimo qualche secondo. */
  function loadVoices(): Promise<void> {
    if (!synth) return Promise.resolve()
    synth.addEventListener?.('voiceschanged', onVoicesChanged)
    loading ??= new Promise((resolve) => {
      const started = Date.now()
      const check = () => {
        if (readVoices() || Date.now() - started >= VOICE_POLL_LIMIT_MS) {
          voicesLoaded.value = true
          resolve()
          return
        }
        setTimeout(check, VOICE_POLL_MS)
      }
      check()
    })
    return loading
  }

  function voicesFor(language: string): VoiceInfo[] {
    return rankVoices(voices.value, language, browserLangs)
  }

  function voiceFor(language: string, savedURI?: string): VoiceInfo | undefined {
    return pickVoice(voices.value, language, savedURI, browserLangs)
  }

  function clearTimers() {
    clearTimeout(timer)
    clearInterval(ticker)
    timer = undefined
    ticker = undefined
    waitRemaining.value = 0
  }

  function interrupt() {
    run++
    clearTimers()
    _activeUtterance = undefined
    synth?.cancel()
  }

  function advance(token: number) {
    if (token !== run) return
    position.value++
    step()
  }

  function step() {
    const token = ++run
    const item = current.value
    if (!item) {
      status.value = 'idle'
      items.value = []
      finish?.('done')
      finish = undefined
      return
    }
    if (item.kind === 'pause') {
      status.value = item.think ? 'waiting' : 'speaking'
      if (item.think) {
        const end = Date.now() + item.ms
        waitRemaining.value = item.ms
        ticker = setInterval(() => {
          waitRemaining.value = Math.max(0, end - Date.now())
        }, COUNTDOWN_TICK_MS)
      }
      timer = setTimeout(() => {
        clearTimers()
        advance(token)
      }, item.ms)
      return
    }
    status.value = 'speaking'
    const utterance = createUtterance(item.text)
    utterance.lang = voice?.lang ?? lang
    utterance.voice = voice ?? null
    utterance.rate = rate.value
    utterance.onend = () => advance(token)
    utterance.onerror = (event) => {
      if (token !== run || OWN_INTERRUPTIONS.has(event.error)) return
      // Voce di rete senza connessione o simili: si resta in pausa, si riprova con un tocco
      _activeUtterance = undefined
      status.value = 'paused'
      error.value = event.error
    }
    _activeUtterance = utterance
    synth?.speak(utterance)
  }

  /**
   * Legge la coda dall'inizio, o da `start`, e si risolve a fine lettura o con stop. Va chiamata
   * da un gesto dell'utente: su iPhone la voce parte solo così, quindi qui non si aspetta nulla.
   */
  function play(
    list: SpeechItem[],
    settings: { lang: string, voiceURI?: string, start?: number },
  ): Promise<PlayResult> {
    stop()
    if (!synth) return Promise.resolve('stopped')
    lang = settings.lang
    voice = voiceFor(settings.lang, settings.voiceURI)
    items.value = list
    position.value = Math.max(0, Math.min(settings.start ?? 0, list.length))
    error.value = undefined
    return new Promise((resolve) => {
      finish = resolve
      step()
    })
  }

  function pause() {
    if (status.value === 'idle' || status.value === 'paused') return
    interrupt()
    status.value = 'paused'
  }

  /** Riparte dall'inizio della frase, o dell'attesa, interrotta. */
  function resume() {
    if (status.value !== 'paused') return
    error.value = undefined
    step()
  }

  /** Salta la frase o l'attesa corrente, per esempio il tempo per pensare a una domanda. */
  function skip() {
    if (status.value === 'idle') return
    interrupt()
    position.value++
    step()
  }

  function stop() {
    interrupt()
    status.value = 'idle'
    items.value = []
    position.value = 0
    finish?.('stopped')
    finish = undefined
  }

  /** La nuova velocità vale subito: la frase in corso riparte dall'inizio. */
  function setRate(value: number) {
    rate.value = value
    if (status.value === 'speaking' && current.value?.kind === 'say') {
      interrupt()
      step()
    }
  }

  if (getCurrentScope()) {
    onScopeDispose(() => {
      stop()
      synth?.removeEventListener?.('voiceschanged', onVoicesChanged)
    })
  }

  return {
    supported,
    voices,
    voicesLoaded,
    status,
    rate,
    current,
    position,
    waitRemaining,
    error,
    loadVoices,
    voicesFor,
    voiceFor,
    play,
    pause,
    resume,
    skip,
    stop,
    setRate,
  }
}
