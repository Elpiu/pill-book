import type { BookPack } from '~/types/bookpack'

/**
 * Ripasso con le scatole di Leitner. Ogni domanda sta in una scatola: se la sai sale e torna più
 * tardi, se non la sai riparte dalla prima.
 */
export const BOX_INTERVAL_DAYS = [1, 3, 7, 16, 35]
const DAY_MS = 24 * 60 * 60 * 1000

export interface ReviewRecord {
  key: string
  bookId: string
  itemId: string
  box: number
  dueAt: string
  lastAt: string
  lapses: number
}

export interface ReviewItem {
  id: string
  bookId: string
  itemId: string
  q: string
  a: string
  page: number | null | undefined
  context: string
}

export function reviewKey(bookId: string, itemId: string): string {
  return `${bookId}::${itemId}`
}

/** Si ragiona a giorni: una domanda dovuta domani è pronta da domattina, non da domani sera. */
function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
}

export function nextReview(
  bookId: string,
  itemId: string,
  known: boolean,
  previous: ReviewRecord | undefined,
  now: Date,
): ReviewRecord {
  const last = BOX_INTERVAL_DAYS.length - 1
  const box = known ? Math.min(previous ? previous.box + 1 : 1, last) : 0
  return {
    key: reviewKey(bookId, itemId),
    bookId,
    itemId,
    box,
    dueAt: new Date(startOfDay(now) + BOX_INTERVAL_DAYS[box]! * DAY_MS).toISOString(),
    lastAt: now.toISOString(),
    lapses: (previous?.lapses ?? 0) + (known ? 0 : 1),
  }
}

/** Tutte le domande ripassabili di un libro: flashcard e domande incontrate durante la lettura. */
export function reviewableItems(pack: BookPack): ReviewItem[] {
  const items: ReviewItem[] = []
  for (const chapter of pack.chapters) {
    const context = `${pack.book.title} · ${chapter.title}`
    const base = { bookId: pack.book.id, context }
    for (const card of chapter.flashcards) {
      items.push({
        ...base,
        id: reviewKey(pack.book.id, card.id),
        itemId: card.id,
        q: card.q,
        a: card.a,
        page: card.page,
      })
    }
    for (const card of chapter.cards) {
      if (card.type === 'check' && card.answer) {
        items.push({
          ...base,
          id: reviewKey(pack.book.id, card.id),
          itemId: card.id,
          q: card.body,
          a: card.answer,
          page: card.page,
        })
      }
    }
  }
  return items
}

/** Le domande da ripassare ora. Quelle sparite da un pack aggiornato si ignorano senza errori. */
export function dueItems(records: ReviewRecord[], packs: BookPack[], now: Date): ReviewItem[] {
  const items = new Map(packs.flatMap(reviewableItems).map(item => [item.id, item]))
  const time = now.getTime()
  return records
    .filter(record => new Date(record.dueAt).getTime() <= time && items.has(record.key))
    .sort((a, b) => a.dueAt.localeCompare(b.dueAt))
    .map(record => items.get(record.key)!)
}

export function nextDueDate(records: ReviewRecord[], packs: BookPack[], now: Date): Date | undefined {
  const items = new Set(packs.flatMap(reviewableItems).map(item => item.id))
  const times = records
    .filter(record => items.has(record.key))
    .map(record => new Date(record.dueAt).getTime())
    .filter(time => time > now.getTime())
  return times.length ? new Date(Math.min(...times)) : undefined
}

/** Tra due stati della stessa domanda vale il più recente. */
export function mergeReview(a: ReviewRecord, b: ReviewRecord): ReviewRecord {
  return b.lastAt > a.lastAt ? b : a
}
