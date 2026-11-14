import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useSpeech } from '~/composables/useSpeech'
import type { SpeechItem, VoiceInfo } from '~/utils/speech'
import { createUtterance, FakeSynth, italian } from './support/fakeSynth'

function setup(voices: VoiceInfo[] = [italian]) {
  const synth = new FakeSynth()
  synth.voices = voices
  const speech = useSpeech({ synth, createUtterance, browserLangs: ['it-IT'] })
  return { synth, speech }
}

const say = (text: string, tag?: string): SpeechItem => (tag ? { kind: 'say', text, tag } : { kind: 'say', text })

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('coda di lettura', () => {
  it('legge le frasi in ordine con la voce della lingua e si risolve alla fine', async () => {
    const { synth, speech } = setup()
    await speech.loadVoices()
    const done = speech.play([say('Uno.'), say('Due.')], { lang: 'it' })
    expect(speech.status.value).toBe('speaking')
    expect(synth.current?.voice).toEqual(italian)
    expect(synth.current?.lang).toBe('it-IT')
    synth.finish()
    synth.finish()
    await expect(done).resolves.toBe('done')
    expect(synth.texts()).toEqual(['Uno.', 'Due.'])
    expect(speech.status.value).toBe('idle')
  })

  it('senza voci per la lingua usa comunque la lingua del libro', () => {
    const { synth, speech } = setup([])
    speech.play([say('Hello.')], { lang: 'en' })
    expect(synth.current?.voice).toBeNull()
    expect(synth.current?.lang).toBe('en')
  })

  it('le pause aspettano il tempo indicato', async () => {
    const { synth, speech } = setup()
    speech.play([say('Prima.'), { kind: 'pause', ms: 700 }, say('Dopo.')], { lang: 'it' })
    synth.finish()
    expect(synth.texts()).toEqual(['Prima.'])
    vi.advanceTimersByTime(699)
    expect(synth.texts()).toEqual(['Prima.'])
    vi.advanceTimersByTime(1)
    expect(synth.texts()).toEqual(['Prima.', 'Dopo.'])
  })

  it('può partire da una posizione', () => {
    const { synth, speech } = setup()
    speech.play([say('Uno.'), say('Due.'), say('Tre.')], { lang: 'it', start: 2 })
    expect(synth.texts()).toEqual(['Tre.'])
  })
})

describe('pausa, ripresa e stop', () => {
  it('la ripresa riparte dall\'inizio della frase interrotta', () => {
    const { synth, speech } = setup()
    speech.play([say('Uno.'), say('Due.')], { lang: 'it' })
    synth.finish()
    speech.pause()
    expect(speech.status.value).toBe('paused')
    expect(synth.current).toBeNull()
    speech.resume()
    expect(synth.texts()).toEqual(['Uno.', 'Due.', 'Due.'])
    expect(speech.status.value).toBe('speaking')
  })

  it('una frase interrotta non fa avanzare la coda', () => {
    const { synth, speech } = setup()
    speech.play([say('Uno.'), say('Due.')], { lang: 'it' })
    const interrupted = synth.current!
    speech.pause()
    interrupted.onend?.()
    expect(speech.position.value).toBe(0)
    expect(synth.texts()).toEqual(['Uno.'])
  })

  it('stop interrompe e risolve la lettura come fermata', async () => {
    const { synth, speech } = setup()
    const done = speech.play([say('Uno.'), say('Due.')], { lang: 'it' })
    speech.stop()
    await expect(done).resolves.toBe('stopped')
    expect(speech.status.value).toBe('idle')
    expect(synth.current).toBeNull()
  })

  it('una nuova lettura ferma quella in corso', async () => {
    const { synth, speech } = setup()
    const first = speech.play([say('Vecchia.')], { lang: 'it' })
    speech.play([say('Nuova.')], { lang: 'it' })
    await expect(first).resolves.toBe('stopped')
    expect(synth.current?.text).toBe('Nuova.')
  })

  it('un errore del sintetizzatore mette in pausa e si riprova con resume', () => {
    const { synth, speech } = setup()
    speech.play([say('Uno.')], { lang: 'it' })
    synth.fail('network')
    expect(speech.status.value).toBe('paused')
    expect(speech.error.value).toBe('network')
    speech.resume()
    expect(speech.error.value).toBeUndefined()
    expect(synth.texts()).toEqual(['Uno.', 'Uno.'])
  })
})

describe('attese da saltare e velocità', () => {
  it('il tempo per pensare mostra il conto alla rovescia e si può saltare', () => {
    const { synth, speech } = setup()
    speech.play([say('Domanda?'), { kind: 'pause', ms: 7000, think: true }, say('Risposta.', 'answer')], { lang: 'it' })
    synth.finish()
    expect(speech.status.value).toBe('waiting')
    expect(speech.waitRemaining.value).toBe(7000)
    vi.advanceTimersByTime(2000)
    expect(speech.waitRemaining.value).toBeLessThanOrEqual(5000)
    speech.skip()
    expect(speech.current.value).toEqual(say('Risposta.', 'answer'))
    expect(synth.texts()).toEqual(['Domanda?', 'Risposta.'])
    vi.advanceTimersByTime(10_000)
    expect(synth.texts()).toEqual(['Domanda?', 'Risposta.'])
  })

  it('una pausa durante l\'attesa la ricomincia alla ripresa', () => {
    const { synth, speech } = setup()
    speech.play([{ kind: 'pause', ms: 7000, think: true }, say('Dopo.')], { lang: 'it' })
    vi.advanceTimersByTime(5000)
    speech.pause()
    vi.advanceTimersByTime(10_000)
    expect(synth.texts()).toEqual([])
    speech.resume()
    vi.advanceTimersByTime(6999)
    expect(synth.texts()).toEqual([])
    vi.advanceTimersByTime(1)
    expect(synth.texts()).toEqual(['Dopo.'])
  })

  it('cambiare velocità fa ripartire la frase in corso con la nuova velocità', () => {
    const { synth, speech } = setup()
    speech.play([say('Uno.')], { lang: 'it' })
    speech.setRate(1.5)
    expect(synth.texts()).toEqual(['Uno.', 'Uno.'])
    expect(synth.current?.rate).toBe(1.5)
  })
})

describe('caricamento delle voci', () => {
  it('aspetta voiceschanged quando l\'elenco iniziale è vuoto', async () => {
    const { synth, speech } = setup([])
    const loaded = speech.loadVoices()
    synth.voices = [italian]
    synth.listeners.forEach(listener => listener())
    vi.advanceTimersByTime(250)
    await loaded
    expect(speech.voices.value).toEqual([italian])
    expect(speech.voiceFor('it')).toEqual(italian)
  })

  it('riprova da solo se voiceschanged non arriva', async () => {
    const { synth, speech } = setup([])
    const loaded = speech.loadVoices()
    vi.advanceTimersByTime(500)
    synth.voices = [italian]
    vi.advanceTimersByTime(250)
    await loaded
    expect(speech.voices.value).toEqual([italian])
  })

  it('smette di aspettare dopo qualche secondo anche senza voci', async () => {
    const { speech } = setup([])
    const loaded = speech.loadVoices()
    vi.advanceTimersByTime(3000)
    await loaded
    expect(speech.voicesLoaded.value).toBe(true)
    expect(speech.voices.value).toEqual([])
  })

  it('senza sintesi vocale non fa nulla', async () => {
    const speech = useSpeech({ synth: undefined, createUtterance, browserLangs: [] })
    expect(speech.supported).toBe(false)
    await expect(speech.play([say('Uno.')], { lang: 'it' })).resolves.toBe('stopped')
  })
})
