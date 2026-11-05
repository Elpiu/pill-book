import { db, type BookRecord } from '~/db'
import type { Chapter } from '~/types/bookpack'
import { chapterState, clampCardIndex, nextChapter, type ProgressRecord } from '~/utils/progress'

export interface LibraryItem {
  record: BookRecord
  progress?: ProgressRecord
}

export interface ResumeTarget {
  item: LibraryItem
  chapter: Chapter
  label: string
}

export function useLibrary() {
  const { data, loaded, error } = useLiveQuery(async () => {
    const [books, progress] = await Promise.all([db.books.toArray(), db.progress.toArray()])
    const byBook = new Map(progress.map(record => [record.bookId, record]))
    return books
      .map((record): LibraryItem => ({ record, progress: byBook.get(record.id) }))
      .sort((a, b) => {
        const dateA = a.progress?.lastOpenedAt ?? a.record.updatedAt
        const dateB = b.progress?.lastOpenedAt ?? b.record.updatedAt
        return dateB.localeCompare(dateA)
      })
  })

  const items = computed(() => data.value ?? [])

  /** L'ultimo libro aperto con ancora qualcosa da leggere. */
  const resume = computed<ResumeTarget | undefined>(() => {
    for (const item of items.value) {
      if (!item.progress?.lastOpenedAt) continue
      const chapter = nextChapter(item.record.pack, item.progress)
      if (!chapter) continue
      const position = chapterState(chapter, item.progress) === 'doing'
        ? describePosition(chapter, item.progress)
        : 'Da iniziare'
      return { item, chapter, label: `Capitolo ${chapter.index}, ${position}` }
    }
    return undefined
  })

  return { items, resume, loaded, error }
}

function describePosition(chapter: Chapter, progress: ProgressRecord): string {
  const saved = progress.chapters[chapter.id]!
  if (saved.phase === 'mindmap') return 'mindmap'
  if (saved.phase === 'flashcards') return 'flashcard'
  return `card ${clampCardIndex(chapter, saved.lastCardIndex) + 1}/${chapter.cards.length}`
}
