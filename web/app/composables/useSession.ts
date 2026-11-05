import { db, recordReview, touchBook, updateChapterProgress } from '~/db'
import type { BookPack, Chapter } from '~/types/bookpack'
import { clampCardIndex, emptyChapterProgress, type ChapterProgress, type FlashResult, type Phase } from '~/utils/progress'

export function useSession(bookId: string, chapterId: string) {
  const status = ref<'loading' | 'missing' | 'ready'>('loading')
  const pack = shallowRef<BookPack>()
  const chapter = shallowRef<Chapter>()
  const phase = ref<Phase>('cards')
  const cardIndex = ref(0)
  const flashResults = ref<Record<string, FlashResult>>({})
  // Un capitolo già completato si può rileggere: la rilettura non sposta il progresso salvato
  const isReview = ref(false)

  function save(update: (saved: ChapterProgress) => ChapterProgress) {
    updateChapterProgress(bookId, chapterId, update).catch((cause) => {
      console.error('Salvataggio del progresso non riuscito', cause)
    })
  }

  async function load() {
    const [record, progress] = await Promise.all([db.books.get(bookId), db.progress.get(bookId)])
    const found = record?.pack.chapters.find(item => item.id === chapterId)
    if (!record || !found) {
      status.value = 'missing'
      return
    }
    pack.value = record.pack
    chapter.value = found

    const saved = progress?.chapters[chapterId] ?? emptyChapterProgress()
    isReview.value = Boolean(saved.completedAt)
    if (!isReview.value) {
      phase.value = saved.phase === 'done' ? 'cards' : saved.phase
      cardIndex.value = clampCardIndex(found, saved.lastCardIndex)
    }
    // Gli esiti di id scomparsi da un pack aggiornato si ignorano senza errori
    const known = new Set([...found.flashcards, ...found.cards].map(card => card.id))
    flashResults.value = isReview.value
      ? {}
      : Object.fromEntries(Object.entries(saved.flashResults ?? {}).filter(([id]) => known.has(id)))

    status.value = 'ready'
    await touchBook(bookId, chapterId)
  }

  function setCard(index: number) {
    cardIndex.value = index
    if (isReview.value) return
    save(saved => ({ ...saved, phase: 'cards', lastCardIndex: index }))
  }

  function goToPhase(next: Phase) {
    phase.value = next
    if (isReview.value || next === 'done') return
    save(saved => ({ ...saved, phase: next, lastCardIndex: cardIndex.value }))
  }

  function recordFlashcard(id: string, known: boolean) {
    const result: FlashResult = { known, at: new Date().toISOString() }
    flashResults.value = { ...flashResults.value, [id]: result }
    save(saved => ({ ...saved, flashResults: { ...saved.flashResults, [id]: result } }))
    recordReview(bookId, id, known).catch((cause) => {
      console.error('Salvataggio del ripasso non riuscito', cause)
    })
  }

  function complete() {
    phase.value = 'done'
    const completedAt = new Date().toISOString()
    save(saved => ({ ...saved, phase: 'done', completedAt: saved.completedAt ?? completedAt }))
  }

  /** Avanzamento complessivo della sessione, da 0 a 100: le card pesano più delle altre fasi. */
  const percent = computed(() => {
    const current = chapter.value
    if (!current) return 0
    switch (phase.value) {
      case 'cards': return Math.round(((cardIndex.value + 1) / current.cards.length) * 70)
      case 'summary': return 72
      case 'mindmap': return 76
      case 'flashcards': {
        const answered = current.flashcards.filter(card => flashResults.value[card.id]).length
        return 80 + Math.round((answered / current.flashcards.length) * 20)
      }
      default: return 100
    }
  })

  return { status, pack, chapter, phase, cardIndex, flashResults, percent, isReview, load, setCard, goToPhase, recordFlashcard, complete }
}
