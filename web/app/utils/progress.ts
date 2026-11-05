import type { BookPack, Chapter } from '~/types/bookpack'

export type Phase = 'cards' | 'mindmap' | 'flashcards' | 'done'

export interface FlashResult {
  known: boolean
  at: string
}

export interface ChapterProgress {
  phase: Phase
  lastCardIndex: number
  completedAt?: string
  flashResults: Record<string, FlashResult>
}

export interface ProgressRecord {
  bookId: string
  currentChapterId?: string
  lastOpenedAt: string
  chapters: Record<string, ChapterProgress>
}

export interface SettingRecord {
  key: string
  value: unknown
}

export type ChapterState = 'todo' | 'doing' | 'done'

const PHASE_ORDER: Phase[] = ['cards', 'mindmap', 'flashcards', 'done']

export function emptyChapterProgress(): ChapterProgress {
  return { phase: 'cards', lastCardIndex: 0, flashResults: {} }
}

/** Indice di card utilizzabile: un pack aggiornato può avere meno card di quelle salvate. */
export function clampCardIndex(chapter: Chapter, index: number): number {
  return Math.min(Math.max(index, 0), chapter.cards.length - 1)
}

export function chapterState(chapter: Chapter, progress?: ProgressRecord): ChapterState {
  const saved = progress?.chapters[chapter.id]
  if (!saved) return 'todo'
  if (saved.completedAt || saved.phase === 'done') return 'done'
  return 'doing'
}

export function chapterStatusLabel(chapter: Chapter, progress?: ProgressRecord): string {
  const state = chapterState(chapter, progress)
  if (state === 'todo') return 'Da iniziare'
  if (state === 'done') return 'Completato'
  const saved = progress!.chapters[chapter.id]!
  if (saved.phase === 'mindmap') return 'In corso: mindmap'
  if (saved.phase === 'flashcards') return 'In corso: flashcard'
  return `In corso: card ${clampCardIndex(chapter, saved.lastCardIndex) + 1}/${chapter.cards.length}`
}

function chapterFraction(chapter: Chapter, progress?: ProgressRecord): number {
  const state = chapterState(chapter, progress)
  if (state === 'todo') return 0
  if (state === 'done') return 1
  const saved = progress!.chapters[chapter.id]!
  if (saved.phase === 'mindmap') return 0.7
  if (saved.phase === 'flashcards') return 0.8
  return (clampCardIndex(chapter, saved.lastCardIndex) / chapter.cards.length) * 0.7
}

export function bookPercent(pack: BookPack, progress?: ProgressRecord): number {
  if (!pack.chapters.length) return 0
  const total = pack.chapters.reduce((sum, chapter) => sum + chapterFraction(chapter, progress), 0)
  return Math.round((total / pack.chapters.length) * 100)
}

/** Il capitolo da suggerire: quello in corso, altrimenti il primo da finire dopo l'attuale. */
export function nextChapter(pack: BookPack, progress?: ProgressRecord): Chapter | undefined {
  const chapters = pack.chapters
  const currentIndex = chapters.findIndex(chapter => chapter.id === progress?.currentChapterId)
  const current = chapters[currentIndex]
  if (current && chapterState(current, progress) === 'doing') return current
  const unfinished = (chapter: Chapter) => chapterState(chapter, progress) !== 'done'
  return chapters.slice(currentIndex + 1).find(unfinished) ?? chapters.find(unfinished)
}

export function chapterAfter(pack: BookPack, chapterId: string): Chapter | undefined {
  const index = pack.chapters.findIndex(chapter => chapter.id === chapterId)
  return index >= 0 ? pack.chapters[index + 1] : undefined
}

// --- Export e import del progresso -------------------------------------------------------------

export const PROGRESS_EXPORT_TYPE = 'bookpack-progress'

export interface ProgressExport {
  type: typeof PROGRESS_EXPORT_TYPE
  version: 1
  exportedAt: string
  progress: ProgressRecord[]
  settings: SettingRecord[]
}

export function parseProgressExport(text: string): ProgressExport {
  let data: Partial<ProgressExport>
  try {
    data = JSON.parse(text)
  }
  catch {
    throw new Error('Il file non è un JSON valido.')
  }
  if (data?.type !== PROGRESS_EXPORT_TYPE || data.version !== 1) {
    throw new Error('Il file non è un export del progresso di Bookpack.')
  }
  if (!Array.isArray(data.progress) || !Array.isArray(data.settings)) {
    throw new Error('L\'export è incompleto: mancano progresso o impostazioni.')
  }
  const valid = data.progress.every(
    item => typeof item?.bookId === 'string' && typeof item.chapters === 'object' && item.chapters !== null,
  )
  if (!valid) throw new Error('L\'export contiene voci di progresso non valide.')
  return data as ProgressExport
}

function isAhead(a: ChapterProgress, b: ChapterProgress): boolean {
  const phaseA = PHASE_ORDER.indexOf(a.phase)
  const phaseB = PHASE_ORDER.indexOf(b.phase)
  return phaseA === phaseB ? a.lastCardIndex > b.lastCardIndex : phaseA > phaseB
}

function mergeChapter(a: ChapterProgress, b: ChapterProgress): ChapterProgress {
  const ahead = isAhead(b, a) ? b : a
  const flashResults = { ...a.flashResults }
  for (const [id, result] of Object.entries(b.flashResults ?? {})) {
    const existing = flashResults[id]
    if (!existing || result.at > existing.at) flashResults[id] = result
  }
  return {
    ...ahead,
    completedAt: a.completedAt ?? b.completedAt,
    flashResults,
  }
}

/** Fonde due progressi dello stesso libro: vale il punto più avanzato e l'esito più recente. */
export function mergeProgress(a: ProgressRecord, b: ProgressRecord): ProgressRecord {
  const chapters = { ...a.chapters }
  for (const [id, chapter] of Object.entries(b.chapters)) {
    const existing = chapters[id]
    chapters[id] = existing ? mergeChapter(existing, chapter) : chapter
  }
  const newest = b.lastOpenedAt > a.lastOpenedAt ? b : a
  return {
    bookId: a.bookId,
    currentChapterId: newest.currentChapterId ?? a.currentChapterId ?? b.currentChapterId,
    lastOpenedAt: newest.lastOpenedAt,
    chapters,
  }
}
