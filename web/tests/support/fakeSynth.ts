import type { SynthLike, UtteranceLike } from '~/composables/useSpeech'
import type { VoiceInfo } from '~/utils/speech'

/** Un sintetizzatore finto: le frasi finiscono quando il test chiama finish(). */
export class FakeSynth implements SynthLike {
  voices: VoiceInfo[] = []
  spoken: UtteranceLike[] = []
  current: UtteranceLike | null = null
  listeners: (() => void)[] = []

  getVoices() {
    return this.voices
  }

  speak(utterance: UtteranceLike) {
    this.spoken.push(utterance)
    this.current = utterance
  }

  // Come i browser: interrompere una frase manda un errore "interrupted"
  cancel() {
    const interrupted = this.current
    this.current = null
    interrupted?.onerror?.({ error: 'interrupted' })
  }

  addEventListener(_type: 'voiceschanged', listener: () => void) {
    this.listeners.push(listener)
  }

  removeEventListener() {}

  finish() {
    const done = this.current
    this.current = null
    done?.onend?.()
  }

  fail(error: string) {
    this.current?.onerror?.({ error })
  }

  texts() {
    return this.spoken.map(utterance => utterance.text)
  }
}

export function createUtterance(text: string): UtteranceLike {
  return { text, lang: '', voice: null, rate: 1, onend: null, onerror: null }
}

export const italian: VoiceInfo = {
  name: 'Alice',
  lang: 'it-IT',
  voiceURI: 'alice',
  localService: true,
  default: false,
}
