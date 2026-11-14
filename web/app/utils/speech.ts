/**
 * Parti pure della sintesi vocale: lingue, frasi e scelta della voce. Non sanno nulla di libri,
 * così si possono riusare e provare senza browser.
 */

/** Cosa leggere: una frase, oppure una pausa. `think` è un'attesa che l'utente può saltare. */
export type SpeechItem =
  | { kind: 'say', text: string, tag?: string }
  | { kind: 'pause', ms: number, think?: boolean, tag?: string }

/** I campi di SpeechSynthesisVoice che servono a scegliere. */
export interface VoiceInfo {
  name: string
  lang: string
  voiceURI: string
  localService: boolean
  default: boolean
}

/**
 * Sopra questa lunghezza una frase si spezza: Chrome interrompe le letture di circa 15 secondi, e
 * 180 caratteri stanno sotto anche a velocità normale.
 */
export const MAX_SENTENCE_CHARS = 180

/** Nomi con cui i sistemi indicano le voci migliori. */
const QUALITY_HINT = /enhanced|premium|natural|neural/i

/** `it_IT`, usato da alcuni Android, diventa `it-IT`; la lingua minuscola, la regione maiuscola. */
export function normalizeLang(tag: string): string {
  const [language = '', region] = tag.trim().replace(/_/g, '-').split('-')
  return region ? `${language.toLowerCase()}-${region.toUpperCase()}` : language.toLowerCase()
}

function primary(tag: string): string {
  return normalizeLang(tag).split('-')[0]!
}

function region(tag: string): string | undefined {
  return normalizeLang(tag).split('-')[1]
}

function splitBySegmenter(text: string, lang: string): string[] | undefined {
  if (typeof Intl === 'undefined' || !('Segmenter' in Intl)) return undefined
  try {
    const segmenter = new Intl.Segmenter(lang || undefined, { granularity: 'sentence' })
    return [...segmenter.segment(text)].map(part => part.segment)
  }
  catch {
    return undefined
  }
}

/** Divide una frase troppo lunga alle pause della punteggiatura e, se non basta, tra le parole. */
function splitLong(sentence: string, max: number): string[] {
  if (sentence.length <= max) return [sentence]
  const pieces = sentence.split(/(?<=[,;:—–])\s+/)
  const result: string[] = []
  let current = ''
  for (const piece of pieces.flatMap(piece => (piece.length > max ? splitWords(piece, max) : [piece]))) {
    if (current && current.length + piece.length + 1 > max) {
      result.push(current)
      current = piece
    }
    else {
      current = current ? `${current} ${piece}` : piece
    }
  }
  if (current) result.push(current)
  return result
}

function splitWords(text: string, max: number): string[] {
  const result: string[] = []
  let current = ''
  for (const word of text.split(/\s+/)) {
    if (current && current.length + word.length + 1 > max) {
      result.push(current)
      current = word
    }
    else {
      current = current ? `${current} ${word}` : word
    }
  }
  if (current) result.push(current)
  return result
}

/** Frasi pronte da leggere una alla volta, nessuna più lunga di `max` caratteri. */
export function splitSentences(text: string, lang = '', max = MAX_SENTENCE_CHARS): string[] {
  const clean = text.replace(/\s+/g, ' ').trim()
  if (!clean) return []
  const sentences = splitBySegmenter(clean, lang) ?? clean.split(/(?<=[.!?…])\s+/)
  return sentences
    .map(sentence => sentence.trim())
    .filter(Boolean)
    .flatMap(sentence => splitLong(sentence, max))
}

/**
 * Voci della lingua chiesta, dalla migliore: stessa regione (quella della lingua o, se manca,
 * quella del browser), poi voci locali che funzionano offline, poi i nomi che indicano qualità,
 * infine la voce predefinita.
 */
export function rankVoices<T extends VoiceInfo>(voices: T[], lang: string, browserLangs: readonly string[] = []): T[] {
  const wanted = primary(lang)
  const wantedRegion = region(lang) ?? browserLangs.filter(tag => primary(tag) === wanted).map(region).find(Boolean)
  const score = (voice: T) => [
    wantedRegion && region(voice.lang) === wantedRegion ? 0 : 1,
    voice.localService ? 0 : 1,
    QUALITY_HINT.test(voice.name) ? 0 : 1,
    voice.default ? 0 : 1,
  ]
  return voices
    .filter(voice => primary(voice.lang) === wanted)
    .map(voice => ({ voice, score: score(voice) }))
    .sort((a, b) => {
      for (let i = 0; i < a.score.length; i++) {
        if (a.score[i] !== b.score[i]) return a.score[i]! - b.score[i]!
      }
      return a.voice.name.localeCompare(b.voice.name)
    })
    .map(({ voice }) => voice)
}

/**
 * Si può ascoltare un libro in questa lingua? Con un elenco vuoto non si sa: alcuni browser non
 * elencano voci ma leggono lo stesso con quella di sistema, quindi si prova.
 */
export function voiceAvailability(voices: VoiceInfo[], lang: string): 'available' | 'missing' | 'unknown' {
  if (!voices.length) return 'unknown'
  return voices.some(voice => primary(voice.lang) === primary(lang)) ? 'available' : 'missing'
}

/** Nome della lingua in italiano, per i messaggi: `en` diventa "inglese". */
export function languageName(lang: string): string {
  try {
    return new Intl.DisplayNames(['it'], { type: 'language' }).of(primary(lang)) ?? lang
  }
  catch {
    return lang
  }
}

/** La voce si ricorda per lingua, senza regione: un libro `it` e uno `it-IT` usano la stessa. */
export function voiceKey(lang: string): string {
  return primary(lang)
}

/** La voce scelta dall'utente se esiste ancora ed è della lingua giusta, altrimenti la migliore. */
export function pickVoice<T extends VoiceInfo>(
  voices: T[],
  lang: string,
  savedURI?: string,
  browserLangs: readonly string[] = [],
): T | undefined {
  const ranked = rankVoices(voices, lang, browserLangs)
  return ranked.find(voice => voice.voiceURI === savedURI) ?? ranked[0]
}
