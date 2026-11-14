import { describe, expect, it } from 'vitest'
import {
  languageName,
  MAX_SENTENCE_CHARS,
  normalizeLang,
  pickVoice,
  rankVoices,
  splitSentences,
  voiceAvailability,
  voiceKey,
  type VoiceInfo,
} from '~/utils/speech'

function voice(name: string, lang: string, extra: Partial<VoiceInfo> = {}): VoiceInfo {
  return { name, lang, voiceURI: name, localService: true, default: false, ...extra }
}

describe('lingue', () => {
  it('rende equivalenti i codici con trattino e con trattino basso', () => {
    expect(normalizeLang('it_IT')).toBe('it-IT')
    expect(normalizeLang('IT-it')).toBe('it-IT')
    expect(normalizeLang(' en ')).toBe('en')
  })
})

describe('frasi', () => {
  it('divide il testo in frasi senza spezzare le abbreviazioni', () => {
    expect(splitSentences('Vedi p. 12 per i dettagli. Poi esegui il comando! Fatto?', 'it')).toEqual([
      'Vedi p. 12 per i dettagli.',
      'Poi esegui il comando!',
      'Fatto?',
    ])
  })

  it('ignora spazi e testo vuoto', () => {
    expect(splitSentences('  \n ')).toEqual([])
    expect(splitSentences('Una   frase\nsu due righe.')).toEqual(['Una frase su due righe.'])
  })

  it('spezza le frasi lunghe alle pause della punteggiatura', () => {
    const long = Array.from({ length: 12 }, (_, i) => `la parte numero ${i + 1} della frase`).join(', ') + '.'
    const pieces = splitSentences(long, 'it')
    expect(pieces.length).toBeGreaterThan(1)
    expect(pieces.every(piece => piece.length <= MAX_SENTENCE_CHARS)).toBe(true)
    expect(pieces.join(' ')).toBe(long)
  })

  it('spezza tra le parole una frase lunga senza punteggiatura', () => {
    const long = 'parola '.repeat(80).trim()
    const pieces = splitSentences(long, 'it', 50)
    expect(pieces.every(piece => piece.length <= 50)).toBe(true)
    expect(pieces.join(' ')).toBe(long)
  })

  it('funziona anche senza Intl.Segmenter', () => {
    const segmenter = Intl.Segmenter
    // @ts-expect-error simula un browser vecchio
    delete Intl.Segmenter
    try {
      expect(splitSentences('Prima frase. Seconda frase!', 'it')).toEqual(['Prima frase.', 'Seconda frase!'])
    }
    finally {
      Intl.Segmenter = segmenter
    }
  })
})

describe('scelta della voce', () => {
  it('tiene solo le voci della lingua chiesta, anche scritte con il trattino basso', () => {
    const voices = [voice('Inglese', 'en-US'), voice('Android', 'it_IT'), voice('Francese', 'fr-FR')]
    expect(rankVoices(voices, 'it').map(v => v.name)).toEqual(['Android'])
  })

  it('preferisce la regione della lingua del browser', () => {
    const voices = [voice('Svizzera', 'it-CH'), voice('Italia', 'it-IT')]
    expect(rankVoices(voices, 'it', ['it-IT', 'en-US'])[0]!.name).toBe('Italia')
    expect(rankVoices(voices, 'it', ['it-CH'])[0]!.name).toBe('Svizzera')
  })

  it('usa la regione della lingua del libro quando c\'è', () => {
    const voices = [voice('Americana', 'en-US'), voice('Britannica', 'en-GB')]
    expect(rankVoices(voices, 'en-GB', ['en-US'])[0]!.name).toBe('Britannica')
  })

  it('preferisce le voci locali, poi quelle migliorate, poi la predefinita', () => {
    const voices = [
      voice('Rete Natural', 'it-IT', { localService: false }),
      voice('Base', 'it-IT'),
      voice('Predefinita', 'it-IT', { default: true }),
      voice('Alice (Enhanced)', 'it-IT'),
    ]
    expect(rankVoices(voices, 'it', ['it-IT']).map(v => v.name)).toEqual([
      'Alice (Enhanced)',
      'Predefinita',
      'Base',
      'Rete Natural',
    ])
  })

  it('la regione conta più del tipo di voce', () => {
    const voices = [voice('Svizzera Premium', 'it-CH'), voice('Italia di rete', 'it-IT', { localService: false })]
    expect(rankVoices(voices, 'it', ['it-IT'])[0]!.name).toBe('Italia di rete')
  })

  it('dice se il libro si può ascoltare nella sua lingua', () => {
    const voices = [voice('Alice', 'it-IT')]
    expect(voiceAvailability(voices, 'it')).toBe('available')
    expect(voiceAvailability(voices, 'en')).toBe('missing')
    // Un elenco vuoto non dice nulla: alcuni browser leggono lo stesso con la voce di sistema
    expect(voiceAvailability([], 'en')).toBe('unknown')
  })

  it('nomina la lingua in italiano e ricorda la voce per lingua senza regione', () => {
    expect(languageName('en')).toBe('inglese')
    expect(languageName('it-IT')).toBe('italiano')
    expect(voiceKey('it_IT')).toBe('it')
  })

  it('rispetta la voce scelta se esiste ancora ed è della lingua giusta', () => {
    const voices = [voice('Alice (Enhanced)', 'it-IT'), voice('Luca', 'it-IT'), voice('Daniel', 'en-GB')]
    expect(pickVoice(voices, 'it', 'Luca')!.name).toBe('Luca')
    expect(pickVoice(voices, 'it', 'Sparita')!.name).toBe('Alice (Enhanced)')
    expect(pickVoice(voices, 'it', 'Daniel')!.name).toBe('Alice (Enhanced)')
    expect(pickVoice(voices, 'de')).toBeUndefined()
  })
})
