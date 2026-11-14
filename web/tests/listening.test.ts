import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { BookPack, Card } from '~/types/bookpack'
import {
  ANSWER_TAG,
  cardScript,
  SECTION_PAUSE_MS,
  STEP_PAUSE_MS,
  summaryScript,
  THINK_MS,
} from '~/utils/listening'
import type { SpeechItem } from '~/utils/speech'

const pack: BookPack = JSON.parse(
  readFileSync(new URL('../public/samples/how-to-live-on-24-hours-a-day.bookpack.json', import.meta.url), 'utf-8'),
)

function card(fields: Partial<Card> & Pick<Card, 'type'>): Card {
  return { id: 'ch-01-c01', body: 'Idea principale.', page: 3, ...fields }
}

function spoken(items: SpeechItem[]): string[] {
  return items.flatMap(item => (item.kind === 'say' ? [item.text] : []))
}

describe('script delle card', () => {
  it('concetto: titolo, idea e spiegazione, con una pausa dopo il titolo', () => {
    const items = cardScript(card({ type: 'concept', title: 'Il tempo', details: 'Si spende una volta.' }), 'it')
    expect(spoken(items)).toEqual(['Il tempo', 'Idea principale.', 'Si spende una volta.'])
    expect(items[1]).toMatchObject({ kind: 'pause' })
  })

  it('il codice resta sullo schermo e non viene letto', () => {
    const items = cardScript(card({ type: 'example', code: 'npm install --save dexie' }), 'it')
    expect(spoken(items).join(' ')).not.toContain('npm')
  })

  it('procedura: i passi uno per volta, con una pausa tra l\'uno e l\'altro, senza backtick', () => {
    const items = cardScript(card({ type: 'procedure', steps: ['Apri il terminale.', 'Esegui `pnpm dev`.'] }), 'it')
    expect(spoken(items)).toEqual(['Idea principale.', 'Apri il terminale.', 'Esegui pnpm dev.'])
    expect(items.filter(item => item.kind === 'pause' && item.ms === STEP_PAUSE_MS)).toHaveLength(2)
  })

  it('domanda: la domanda, 7 secondi per pensare saltabili, poi la risposta marcata', () => {
    const items = cardScript(card({ type: 'check', body: 'Perché conta?', answer: 'Perché non torna.' }), 'it')
    expect(items).toEqual([
      { kind: 'say', text: 'Perché conta?' },
      { kind: 'pause', ms: THINK_MS, think: true },
      { kind: 'say', text: 'Perché non torna.', tag: ANSWER_TAG },
    ])
    expect(THINK_MS).toBe(7000)
  })

  it('nuova parte: titolo e introduzione, poi una pausa più lunga', () => {
    const items = cardScript(card({ type: 'section', title: 'Parte 2' }), 'it')
    expect(spoken(items)).toEqual(['Parte 2', 'Idea principale.'])
    expect(items.at(-1)).toEqual({ kind: 'pause', ms: SECTION_PAUSE_MS })
  })

  it('citazione e takeaway: solo il testo', () => {
    expect(spoken(cardScript(card({ type: 'quote', body: 'Il tempo è denaro.' }), 'it'))).toEqual(['Il tempo è denaro.'])
    expect(spoken(cardScript(card({ type: 'takeaway', body: 'Comincia domani.' }), 'it'))).toEqual(['Comincia domani.'])
  })

  it('legge solo testo del libro: ogni frase di ogni card del pack d\'esempio viene dalla card', () => {
    for (const chapter of pack.chapters) {
      for (const item of chapter.cards) {
        const source = [item.title, item.body, item.details, item.answer, ...(item.steps ?? [])]
          .filter(Boolean)
          .join(' ')
          .replace(/\s+/g, ' ')
        for (const sentence of spoken(cardScript(item, pack.book.lang))) {
          expect(source).toContain(sentence)
        }
      }
    }
  })
})

describe('script del riassunto', () => {
  it('legge tutti i paragrafi con una pausa tra l\'uno e l\'altro', () => {
    const items = summaryScript('Primo paragrafo. Due frasi.\n\nSecondo paragrafo.', 'it')
    expect(spoken(items)).toEqual(['Primo paragrafo.', 'Due frasi.', 'Secondo paragrafo.'])
    expect(items.filter(item => item.kind === 'pause')).toHaveLength(1)
  })

  it('il riassunto vero diventa frasi brevi', () => {
    const items = summaryScript(pack.chapters[0]!.summary, pack.book.lang)
    expect(spoken(items).length).toBeGreaterThan(3)
  })
})
