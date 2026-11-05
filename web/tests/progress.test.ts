import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { BookPack } from '~/types/bookpack'
import {
  bookPercent,
  chapterAfter,
  chapterState,
  chapterStatusLabel,
  clampCardIndex,
  mergeProgress,
  nextChapter,
  parseProgressExport,
  sectionPosition,
  sessionPhases,
  type ProgressRecord,
} from '~/utils/progress'

const pack: BookPack = JSON.parse(
  readFileSync(new URL('../public/samples/how-to-live-on-24-hours-a-day.bookpack.json', import.meta.url), 'utf-8'),
)
const [first, second, third] = pack.chapters

function progress(chapters: ProgressRecord['chapters'], current?: string, at = '2026-01-01'): ProgressRecord {
  return { bookId: pack.book.id, currentChapterId: current, lastOpenedAt: at, chapters }
}
const inCards = (index: number) => ({ phase: 'cards' as const, lastCardIndex: index, flashResults: {} })
const done = () => ({ phase: 'done' as const, lastCardIndex: 0, completedAt: '2026-01-01', flashResults: {} })

describe('stato dei capitoli', () => {
  it('distingue da iniziare, in corso e completato', () => {
    expect(chapterState(first!, undefined)).toBe('todo')
    expect(chapterStatusLabel(first!, undefined)).toBe('Da iniziare')
    const saved = progress({ [first!.id]: inCards(3), [second!.id]: done() })
    expect(chapterStatusLabel(first!, saved)).toBe(`In corso: card 4/${first!.cards.length}`)
    expect(chapterState(second!, saved)).toBe('done')
  })

  it('ignora una posizione oltre le card di un pack aggiornato', () => {
    expect(clampCardIndex(first!, 999)).toBe(first!.cards.length - 1)
    const saved = progress({ [first!.id]: inCards(999) })
    expect(chapterStatusLabel(first!, saved)).toBe(`In corso: card ${first!.cards.length}/${first!.cards.length}`)
  })

  it('ignora il progresso di capitoli che non esistono più', () => {
    const saved = progress({ 'ch-99': done() }, 'ch-99')
    expect(bookPercent(pack, saved)).toBe(0)
    expect(nextChapter(pack, saved)?.id).toBe(first!.id)
  })
})

describe('capitolo suggerito', () => {
  it('parte dal primo', () => {
    expect(nextChapter(pack, undefined)?.id).toBe(first!.id)
  })

  it('resta su quello in corso', () => {
    expect(nextChapter(pack, progress({ [second!.id]: inCards(1) }, second!.id))?.id).toBe(second!.id)
  })

  it('passa al successivo dopo il completamento', () => {
    expect(nextChapter(pack, progress({ [first!.id]: done() }, first!.id))?.id).toBe(second!.id)
  })

  it('torna indietro ai capitoli saltati quando arriva in fondo', () => {
    const chapters = Object.fromEntries(pack.chapters.slice(1).map(chapter => [chapter.id, done()]))
    expect(nextChapter(pack, progress(chapters, pack.chapters.at(-1)!.id))?.id).toBe(first!.id)
  })

  it('non suggerisce nulla a libro finito', () => {
    const chapters = Object.fromEntries(pack.chapters.map(chapter => [chapter.id, done()]))
    expect(nextChapter(pack, progress(chapters, first!.id))).toBeUndefined()
    expect(bookPercent(pack, progress(chapters))).toBe(100)
  })

  it('trova il capitolo dopo', () => {
    expect(chapterAfter(pack, first!.id)?.id).toBe(second!.id)
    expect(chapterAfter(pack, pack.chapters.at(-1)!.id)).toBeUndefined()
  })
})

describe('fusione del progresso', () => {
  it('tiene il punto più avanzato, i capitoli di entrambi e l\'esito più recente', () => {
    const a = progress({
      [first!.id]: { ...inCards(5), flashResults: { f1: { known: false, at: '2026-01-01' }, f2: { known: true, at: '2026-03-01' } } },
      [second!.id]: inCards(1),
    }, first!.id, '2026-02-01')
    const b = progress({
      [first!.id]: { ...inCards(2), flashResults: { f1: { known: true, at: '2026-02-01' }, f2: { known: false, at: '2026-01-01' } } },
      [second!.id]: { phase: 'mindmap', lastCardIndex: 0, flashResults: {} },
      [third!.id]: done(),
    }, third!.id, '2026-03-01')

    const merged = mergeProgress(a, b)
    expect(merged.chapters[first!.id]!.lastCardIndex).toBe(5)
    expect(merged.chapters[first!.id]!.flashResults).toEqual({
      f1: { known: true, at: '2026-02-01' },
      f2: { known: true, at: '2026-03-01' },
    })
    expect(merged.chapters[second!.id]!.phase).toBe('mindmap')
    expect(merged.chapters[third!.id]!.completedAt).toBeDefined()
    expect(merged.currentChapterId).toBe(third!.id)
    expect(merged.lastOpenedAt).toBe('2026-03-01')
  })

  it('conserva il completamento anche se l\'altro lato è più indietro', () => {
    const merged = mergeProgress(
      progress({ [first!.id]: done() }),
      progress({ [first!.id]: inCards(2) }, undefined, '2026-05-01'),
    )
    expect(merged.chapters[first!.id]!.completedAt).toBe('2026-01-01')
    expect(merged.chapters[first!.id]!.phase).toBe('done')
  })
})

describe('parseProgressExport', () => {
  const good = { type: 'bookpack-progress', version: 1, exportedAt: 'x', progress: [{ bookId: 'a', chapters: {} }], settings: [] }

  it('accetta un export valido', () => {
    expect(parseProgressExport(JSON.stringify(good)).progress).toHaveLength(1)
  })

  it.each([
    ['{ nope', 'JSON'],
    ['{"type":"altro"}', 'export'],
    [JSON.stringify({ ...good, progress: 'x' }), 'incompleto'],
    [JSON.stringify({ ...good, progress: [{ foo: 1 }] }), 'non valide'],
  ])('rifiuta %s', (text, message) => {
    expect(() => parseProgressExport(text)).toThrow(message)
  })
})

describe('fasi e parti', () => {
  it('inserisce il riassunto dopo le card, se c\'è', () => {
    expect(sessionPhases(first!)).toEqual(['cards', 'summary', 'mindmap', 'flashcards'])
    expect(sessionPhases({ ...first!, summary: undefined as unknown as string })).toEqual(['cards', 'mindmap', 'flashcards'])
  })

  it('mostra la fase del riassunto nello stato', () => {
    const saved = progress({ [first!.id]: { phase: 'summary', lastCardIndex: 0, flashResults: {} } })
    expect(chapterStatusLabel(first!, saved)).toBe('In corso: riassunto')
  })

  it('conta le parti di un capitolo lungo', () => {
    const card = (id: string, type: 'section' | 'concept') => ({ id, type, body: 'x', page: 1 })
    const chapter = {
      ...first!,
      cards: [card('a', 'section'), card('b', 'concept'), card('c', 'section'), card('d', 'concept')],
    }
    expect(sectionPosition(chapter, 0)).toEqual({ current: 1, total: 2 })
    expect(sectionPosition(chapter, 1)).toEqual({ current: 1, total: 2 })
    expect(sectionPosition(chapter, 3)).toEqual({ current: 2, total: 2 })
    expect(sectionPosition({ ...first!, cards: [card('b', 'concept')] }, 0)).toBeUndefined()
  })

  it('accetta gli export della versione precedente, senza ripassi', () => {
    const old = { type: 'bookpack-progress', version: 1, exportedAt: 'x', progress: [], settings: [] }
    expect(parseProgressExport(JSON.stringify(old)).reviews).toBeUndefined()
  })
})
