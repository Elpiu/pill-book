import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { BookPack } from '~/types/bookpack'
import {
  BOX_INTERVAL_DAYS,
  dueItems,
  mergeReview,
  nextDueDate,
  nextReview,
  reviewableItems,
  reviewKey,
  type ReviewRecord,
} from '~/utils/review'

const pack: BookPack = JSON.parse(
  readFileSync(new URL('../public/samples/how-to-live-on-24-hours-a-day.bookpack.json', import.meta.url), 'utf-8'),
)
const bookId = pack.book.id
const flashcard = pack.chapters[0]!.flashcards[0]!
const now = new Date(2026, 10, 10, 20, 30)

function daysFrom(date: Date, iso: string): number {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
  return Math.round((new Date(iso).getTime() - start) / 86_400_000)
}

describe('intervalli', () => {
  it('una domanda saputa la prima volta torna dopo qualche giorno', () => {
    const record = nextReview(bookId, flashcard.id, true, undefined, now)
    expect(record.box).toBe(1)
    expect(daysFrom(now, record.dueAt)).toBe(BOX_INTERVAL_DAYS[1])
  })

  it('una domanda non saputa torna domani', () => {
    const record = nextReview(bookId, flashcard.id, false, undefined, now)
    expect(record.box).toBe(0)
    expect(record.lapses).toBe(1)
    expect(daysFrom(now, record.dueAt)).toBe(1)
  })

  it('sale di scatola finché la sai e riparte quando la sbagli', () => {
    let record: ReviewRecord | undefined
    for (let i = 0; i < 8; i++) record = nextReview(bookId, flashcard.id, true, record, now)
    expect(record!.box).toBe(BOX_INTERVAL_DAYS.length - 1)
    expect(daysFrom(now, record!.dueAt)).toBe(35)

    record = nextReview(bookId, flashcard.id, false, record, now)
    expect(record.box).toBe(0)
    expect(record.lapses).toBe(1)
  })

  it('è pronta dal mattino del giorno dovuto, non dalla stessa ora', () => {
    const record = nextReview(bookId, flashcard.id, false, undefined, now)
    const nextMorning = new Date(2026, 10, 11, 7, 0)
    expect(dueItems([record], [pack], nextMorning)).toHaveLength(1)
    expect(dueItems([record], [pack], new Date(2026, 10, 10, 23, 0))).toHaveLength(0)
  })
})

describe('domande da ripassare', () => {
  it('comprende flashcard e domande della lettura', () => {
    const items = reviewableItems(pack)
    const checks = pack.chapters.flatMap(chapter => chapter.cards).filter(card => card.type === 'check')
    const flashcards = pack.chapters.flatMap(chapter => chapter.flashcards)
    expect(items).toHaveLength(checks.length + flashcards.length)
    expect(checks.length).toBeGreaterThan(0)
    const check = items.find(item => item.itemId === checks[0]!.id)!
    expect(check.q).toBe(checks[0]!.body)
    expect(check.a).toBe(checks[0]!.answer)
    expect(check.context).toContain(pack.book.title)
  })

  it('ignora le domande sparite da un pack aggiornato', () => {
    const gone = nextReview(bookId, 'ch-99-f01', false, undefined, now)
    const later = new Date(2026, 10, 20)
    expect(dueItems([gone], [pack], later)).toEqual([])
    expect(nextDueDate([gone], [pack], now)).toBeUndefined()
  })

  it('ordina dalla più arretrata e indica la prossima data', () => {
    const second = pack.chapters[0]!.flashcards[1]!
    const older = nextReview(bookId, second.id, false, undefined, new Date(2026, 10, 1))
    const newer = nextReview(bookId, flashcard.id, false, undefined, new Date(2026, 10, 5))
    const items = dueItems([newer, older], [pack], new Date(2026, 10, 10))
    expect(items.map(item => item.itemId)).toEqual([second.id, flashcard.id])
    expect(nextDueDate([newer, older], [pack], new Date(2026, 10, 3))?.getDate()).toBe(6)
  })
})

describe('fusione', () => {
  it('vale l\'esito più recente', () => {
    const older = nextReview(bookId, flashcard.id, true, undefined, new Date(2026, 10, 1))
    const newer = nextReview(bookId, flashcard.id, false, undefined, new Date(2026, 10, 5))
    expect(mergeReview(older, newer)).toBe(newer)
    expect(mergeReview(newer, older)).toBe(newer)
    expect(reviewKey(bookId, flashcard.id)).toBe(older.key)
  })
})
