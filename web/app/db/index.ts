import Dexie, { type EntityTable } from 'dexie'
import type { BookPack } from '~/types/bookpack'
import {
  emptyChapterProgress,
  mergeProgress,
  PROGRESS_EXPORT_TYPE,
  type ChapterProgress,
  type ProgressExport,
  type ProgressRecord,
  type SettingRecord,
} from '~/utils/progress'
import { mergeReview, nextReview, reviewKey, type ReviewRecord } from '~/utils/review'

export interface BookRecord {
  id: string
  pack: BookPack
  importedAt: string
  updatedAt: string
}

export const db = new Dexie('bookpack') as Dexie & {
  books: EntityTable<BookRecord, 'id'>
  progress: EntityTable<ProgressRecord, 'bookId'>
  settings: EntityTable<SettingRecord, 'key'>
  reviews: EntityTable<ReviewRecord, 'key'>
}

db.version(1).stores({
  books: 'id, updatedAt',
  progress: 'bookId, lastOpenedAt',
  settings: 'key',
})

db.version(2).stores({
  reviews: 'key, dueAt, bookId',
})

/** Salva un pack. Il progresso è indicizzato per id stabili, quindi sopravvive all'aggiornamento. */
export async function saveBook(pack: BookPack): Promise<void> {
  const now = new Date().toISOString()
  const existing = await db.books.get(pack.book.id)
  await db.books.put({
    id: pack.book.id,
    pack,
    importedAt: existing?.importedAt ?? now,
    updatedAt: now,
  })
  // Senza questa richiesta il browser può cancellare libri e progresso se manca spazio
  navigator.storage?.persist?.().catch(() => undefined)
}

export async function deleteBook(bookId: string): Promise<void> {
  await db.transaction('rw', db.books, db.progress, db.reviews, async () => {
    await db.books.delete(bookId)
    await db.progress.delete(bookId)
    await db.reviews.where('bookId').equals(bookId).delete()
  })
}

export async function resetProgress(bookId?: string): Promise<void> {
  await db.transaction('rw', db.progress, db.reviews, async () => {
    if (bookId) {
      await db.progress.delete(bookId)
      await db.reviews.where('bookId').equals(bookId).delete()
    }
    else {
      await db.progress.clear()
      await db.reviews.clear()
    }
  })
}

export async function touchBook(bookId: string, currentChapterId?: string): Promise<void> {
  await db.transaction('rw', db.progress, async () => {
    const record = await db.progress.get(bookId)
    await db.progress.put({
      bookId,
      chapters: record?.chapters ?? {},
      currentChapterId: currentChapterId ?? record?.currentChapterId,
      lastOpenedAt: new Date().toISOString(),
    })
  })
}

export async function updateChapterProgress(
  bookId: string,
  chapterId: string,
  update: (chapter: ChapterProgress) => ChapterProgress,
): Promise<void> {
  await db.transaction('rw', db.progress, async () => {
    const record = await db.progress.get(bookId)
    const chapters = record?.chapters ?? {}
    await db.progress.put({
      bookId,
      currentChapterId: chapterId,
      lastOpenedAt: new Date().toISOString(),
      chapters: { ...chapters, [chapterId]: update(chapters[chapterId] ?? emptyChapterProgress()) },
    })
  })
}

export async function getSetting<T>(key: string): Promise<T | undefined> {
  return (await db.settings.get(key))?.value as T | undefined
}

export async function setSetting(key: string, value: unknown): Promise<void> {
  await db.settings.put({ key, value })
}

/** Registra un esito e fissa quando la domanda dovrà tornare. */
export async function recordReview(bookId: string, itemId: string, known: boolean, now = new Date()): Promise<void> {
  await db.transaction('rw', db.reviews, async () => {
    const previous = await db.reviews.get(reviewKey(bookId, itemId))
    await db.reviews.put(nextReview(bookId, itemId, known, previous, now))
  })
}

export async function exportProgress(): Promise<ProgressExport> {
  return {
    type: PROGRESS_EXPORT_TYPE,
    version: 2,
    exportedAt: new Date().toISOString(),
    progress: await db.progress.toArray(),
    settings: await db.settings.toArray(),
    reviews: await db.reviews.toArray(),
  }
}

export async function importProgress(data: ProgressExport, mode: 'merge' | 'replace'): Promise<void> {
  const reviews = data.reviews ?? []
  await db.transaction('rw', db.progress, db.settings, db.reviews, async () => {
    if (mode === 'replace') {
      await db.progress.clear()
      await db.settings.clear()
      await db.reviews.clear()
      await db.progress.bulkPut(data.progress)
      await db.settings.bulkPut(data.settings)
      await db.reviews.bulkPut(reviews)
      return
    }
    for (const incoming of data.progress) {
      const existing = await db.progress.get(incoming.bookId)
      await db.progress.put(existing ? mergeProgress(existing, incoming) : incoming)
    }
    await db.settings.bulkPut(data.settings)
    for (const incoming of reviews) {
      const existing = await db.reviews.get(incoming.key)
      await db.reviews.put(existing ? mergeReview(existing, incoming) : incoming)
    }
  })
}
