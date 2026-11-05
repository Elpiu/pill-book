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
}

db.version(1).stores({
  books: 'id, updatedAt',
  progress: 'bookId, lastOpenedAt',
  settings: 'key',
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
}

export async function deleteBook(bookId: string): Promise<void> {
  await db.transaction('rw', db.books, db.progress, async () => {
    await db.books.delete(bookId)
    await db.progress.delete(bookId)
  })
}

export async function resetProgress(bookId?: string): Promise<void> {
  if (bookId) await db.progress.delete(bookId)
  else await db.progress.clear()
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

export async function exportProgress(): Promise<ProgressExport> {
  return {
    type: PROGRESS_EXPORT_TYPE,
    version: 1,
    exportedAt: new Date().toISOString(),
    progress: await db.progress.toArray(),
    settings: await db.settings.toArray(),
  }
}

export async function importProgress(data: ProgressExport, mode: 'merge' | 'replace'): Promise<void> {
  await db.transaction('rw', db.progress, db.settings, async () => {
    if (mode === 'replace') {
      await db.progress.clear()
      await db.settings.clear()
      await db.progress.bulkPut(data.progress)
      await db.settings.bulkPut(data.settings)
      return
    }
    for (const incoming of data.progress) {
      const existing = await db.progress.get(incoming.bookId)
      await db.progress.put(existing ? mergeProgress(existing, incoming) : incoming)
    }
    await db.settings.bulkPut(data.settings)
  })
}
