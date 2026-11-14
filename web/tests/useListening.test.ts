import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useListening } from '~/composables/useListening'
import { useSpeech } from '~/composables/useSpeech'
import type { Card } from '~/types/bookpack'
import { THINK_MS } from '~/utils/listening'
import { createUtterance, FakeSynth, italian } from './support/fakeSynth'

const cards: Card[] = [
  { id: 'c1', type: 'concept', title: 'Primo', body: 'Idea uno.' },
  { id: 'c2', type: 'check', body: 'Perché?', answer: 'Perché sì.' },
  { id: 'c3', type: 'takeaway', body: 'Fine.' },
]
const summary = 'Riassunto del capitolo.'

/** Lascia girare le promesse in coda: la regia passa alla card dopo con un await. */
async function flush() {
  for (let i = 0; i < 5; i++) await Promise.resolve()
}

function setup() {
  const synth = new FakeSynth()
  synth.voices = [italian]
  const speech = useSpeech({ synth, createUtterance, browserLangs: ['it-IT'] })
  const events: string[] = []
  const listening = useListening({
    speech,
    cards: () => cards,
    summary: () => summary,
    lang: () => 'it',
    voiceURI: () => undefined,
    onCard: index => events.push(`card ${index}`),
    onSummary: () => events.push('riassunto'),
    onFinished: () => events.push('fine'),
  })
  return { synth, speech, listening, events }
}

/** Fa finire tutte le frasi della card corrente, attese comprese. */
async function finishCard(synth: FakeSynth) {
  for (let i = 0; i < 10; i++) {
    if (synth.current) synth.finish()
    else vi.runOnlyPendingTimers()
    await flush()
  }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('regia dell\'ascolto', () => {
  it('legge le card una dopo l\'altra, poi il riassunto, poi si ferma', async () => {
    const { synth, listening, events } = setup()
    listening.start(0)
    expect(listening.active.value).toBe(true)
    expect(synth.current?.text).toBe('Primo')
    await finishCard(synth)
    expect(events).toEqual(['card 0', 'card 1', 'card 2', 'riassunto', 'fine'])
    expect(listening.active.value).toBe(false)
    expect(synth.texts()).toEqual(['Primo', 'Idea uno.', 'Perché?', 'Perché sì.', 'Fine.', 'Riassunto del capitolo.'])
  })

  it('durante una domanda aspetta 7 secondi, poi mostra e legge la risposta', async () => {
    const { synth, speech, listening } = setup()
    listening.start(1)
    synth.finish()
    await flush()
    expect(speech.status.value).toBe('waiting')
    expect(listening.revealedCardId.value).toBeUndefined()
    vi.advanceTimersByTime(THINK_MS)
    expect(synth.current?.text).toBe('Perché sì.')
    expect(listening.revealedCardId.value).toBe('c2')
  })

  it('l\'attesa di una domanda si può saltare', async () => {
    const { synth, listening } = setup()
    listening.start(1)
    synth.finish()
    await flush()
    listening.skipWait()
    expect(synth.current?.text).toBe('Perché sì.')
  })

  it('segnala la card in lettura', () => {
    const { listening } = setup()
    expect(listening.listeningCardId.value).toBeUndefined()
    listening.start(2)
    expect(listening.listeningCardId.value).toBe('c3')
  })

  it('uno spostamento dell\'utente fa ripartire la voce dalla card raggiunta', async () => {
    const { synth, listening, events } = setup()
    listening.start(0)
    listening.userMoved(2)
    await flush()
    expect(synth.current?.text).toBe('Fine.')
    expect(events).toEqual(['card 0', 'card 2'])
  })

  it('ignora lo spostamento che ha chiesto lei stessa', () => {
    const { synth, listening } = setup()
    listening.start(0)
    listening.userMoved(0)
    expect(synth.texts()).toEqual(['Primo'])
  })

  it('senza ascolto attivo gli spostamenti non fanno nulla', () => {
    const { synth, listening } = setup()
    listening.userMoved(1)
    listening.next()
    expect(synth.texts()).toEqual([])
  })

  it('avanti e indietro passano tra card, riassunto e fine', async () => {
    const { synth, listening, events } = setup()
    listening.start(2)
    listening.next()
    await flush()
    expect(listening.part.value).toBe('summary')
    expect(synth.current?.text).toBe('Riassunto del capitolo.')
    listening.prev()
    await flush()
    expect(synth.current?.text).toBe('Fine.')
    listening.next()
    await flush()
    listening.next()
    await flush()
    expect(events.at(-1)).toBe('fine')
    expect(listening.active.value).toBe(false)
  })

  it('pausa e ripresa', async () => {
    const { synth, speech, listening } = setup()
    listening.start(0)
    listening.toggle()
    expect(speech.status.value).toBe('paused')
    listening.toggle()
    expect(speech.status.value).toBe('speaking')
    expect(synth.texts()).toEqual(['Primo', 'Primo'])
  })

  it('chiudere ferma la voce senza passare alla card dopo', async () => {
    const { synth, speech, listening, events } = setup()
    listening.start(0)
    listening.close()
    await flush()
    expect(listening.active.value).toBe(false)
    expect(speech.status.value).toBe('idle')
    expect(synth.current).toBeNull()
    expect(events).toEqual(['card 0'])
  })

  it('può partire dal riassunto', async () => {
    const { synth, listening, events } = setup()
    listening.start(cards.length)
    expect(events).toEqual(['riassunto'])
    expect(synth.current?.text).toBe('Riassunto del capitolo.')
  })
})
