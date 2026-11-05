import { db, type BookRecord } from '~/db'
import type { Chapter } from '~/types/bookpack'
import { chapterState, clampCardIndex, nextChapter, type ProgressRecord } from '~/utils/progress'
import { dueItems } from '~/utils/review'

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
    const [books, progress, reviews] = await Promise.all([
      db.books.toArray(),
      db.progress.toArray(),
      db.reviews.toArray(),
    ])
    const byBook = new Map(progress.map(record => [record.bookId, record]))
    const due = dueItems(reviews, books.map(book => book.pack), new Date()).length
    const items = books
      .map((record): LibraryItem => ({ record, progress: byBook.get(record.id) }))
      .sort((a, b) => {
        const dateA = a.progress?.lastOpenedAt ?? a.record.updatedAt
        const dateB = b.progress?.lastOpenedAt ?? b.record.updatedAt
        return dateB.localeCompare(dateA)
      })
    return { items, due }
  })

  const items = computed(() => data.value?.items ?? [])
  const dueCount = computed(() => data.value?.due ?? 0)

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

  return { items, resume, dueCount, loaded, error }
}

function describePosition(chapter: Chapter, progress: ProgressRecord): string {
  const saved = progress.chapters[chapter.id]!
  if (saved.phase === 'summary') return 'riassunto'
  if (saved.phase === 'mindmap') return 'mindmap'
  if (saved.phase === 'flashcards') return 'flashcard'
  return `card ${clampCardIndex(chapter, saved.lastCardIndex) + 1}/${chapter.cards.length}`
}
