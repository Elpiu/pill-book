import { getSetting, setSetting } from '~/db'
import { voiceKey } from '~/utils/speech'

/** Velocità tra cui si sceglie in ascolto, in ordine: il pulsante le scorre. */
export const LISTEN_RATES = [0.8, 1, 1.2, 1.5]

/**
 * Preferenze dell'ascolto. Stanno nella tabella settings come le altre, quindi entrano anche
 * nell'export del progresso.
 */
export function useListenSettings() {
  const showButton = useState('listen-show-button', () => true)
  const rate = useState('listen-rate', () => 1)
  /** voiceURI scelto, per lingua senza regione. */
  const voices = useState<Record<string, string>>('listen-voices', () => ({}))

  async function restore() {
    const [savedShow, savedRate, savedVoices] = await Promise.all([
      getSetting<boolean>('listenShowButton'),
      getSetting<number>('listenRate'),
      getSetting<Record<string, string>>('listenVoices'),
    ])
    if (typeof savedShow === 'boolean') showButton.value = savedShow
    if (typeof savedRate === 'number' && LISTEN_RATES.includes(savedRate)) rate.value = savedRate
    if (savedVoices && typeof savedVoices === 'object') voices.value = savedVoices
  }

  async function setShowButton(value: boolean) {
    showButton.value = value
    await setSetting('listenShowButton', value)
  }

  async function setRate(value: number) {
    rate.value = value
    await setSetting('listenRate', value)
  }

  /** Senza voiceURI si torna alla scelta automatica. */
  async function setVoice(lang: string, voiceURI?: string) {
    const key = voiceKey(lang)
    const next = Object.fromEntries(Object.entries(voices.value).filter(([saved]) => saved !== key))
    if (voiceURI) next[key] = voiceURI
    voices.value = next
    await setSetting('listenVoices', next)
  }

  function voiceFor(lang: string): string | undefined {
    return voices.value[voiceKey(lang)]
  }

  return { showButton, rate, voices, restore, setShowButton, setRate, setVoice, voiceFor }
}
