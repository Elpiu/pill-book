import { addActivity } from '~/db'
import type { ActivityRecord } from '~/utils/routine'

/**
 * Minuti di lettura attiva: pagina visibile e utente presente, cioè un'interazione negli ultimi
 * 3 minuti (una card densa si legge a lungo senza toccare) oppure l'ascolto in corso.
 */

export const IDLE_MS = 3 * 60 * 1000
export const TICK_MS = 5000
export const FLUSH_EVERY_MS = 30_000

export interface ActiveTimerOptions {
  now?: () => number
  isVisible: () => boolean
  isListening?: () => boolean
  /** Riceve secondi interi; il resto aspetta il salvataggio successivo. */
  onFlush: (seconds: number) => void
}

export function createActiveTimer(options: ActiveTimerOptions) {
  const now = options.now ?? Date.now
  let lastInteraction = now()
  let lastTick = now()
  let lastFlush = now()
  let pendingMs = 0

  function isPresent(at: number): boolean {
    return Boolean(options.isListening?.()) || at - lastInteraction <= IDLE_MS
  }

  function flush() {
    const seconds = Math.floor(pendingMs / 1000)
    lastFlush = now()
    if (seconds <= 0) return
    pendingMs -= seconds * 1000
    options.onFlush(seconds)
  }

  return {
    interaction() {
      lastInteraction = now()
    },
    tick() {
      const at = now()
      // In background i timer rallentano: un salto lungo non è tempo di lettura
      const elapsed = Math.min(at - lastTick, TICK_MS * 2)
      lastTick = at
      if (elapsed > 0 && options.isVisible() && isPresent(at)) pendingMs += elapsed
      if (at - lastFlush >= FLUSH_EVERY_MS) flush()
    },
    /** Dopo un periodo nascosto si riparte da adesso. */
    resume() {
      lastTick = now()
    },
    flush,
  }
}

const INTERACTIONS = ['pointerdown', 'keydown', 'wheel', 'touchstart', 'scroll'] as const

/** Conta i minuti nella pagina che lo usa e li aggiunge al registro di oggi. */
export function useReadingTimer(options: {
  isListening?: () => boolean
  onGoalReached?: (record: ActivityRecord) => void
} = {}) {
  let interval: ReturnType<typeof setInterval> | undefined
  const timer = createActiveTimer({
    isVisible: () => document.visibilityState === 'visible',
    isListening: options.isListening,
    onFlush(seconds) {
      addActivity({ seconds })
        .then((result) => {
          if (result.reachedGoal) options.onGoalReached?.(result.record)
        })
        .catch((cause) => {
          console.error('Minuti di lettura non salvati', cause)
        })
    },
  })
  const onInteraction = () => timer.interaction()
  const onVisibility = () => {
    if (document.visibilityState === 'hidden') timer.flush()
    else timer.resume()
  }
  const onPageHide = () => timer.flush()

  onMounted(() => {
    for (const type of INTERACTIONS) window.addEventListener(type, onInteraction, { capture: true, passive: true })
    document.addEventListener('visibilitychange', onVisibility)
    window.addEventListener('pagehide', onPageHide)
    interval = setInterval(() => timer.tick(), TICK_MS)
  })

  onBeforeUnmount(() => {
    clearInterval(interval)
    timer.tick()
    timer.flush()
    for (const type of INTERACTIONS) window.removeEventListener(type, onInteraction, { capture: true })
    document.removeEventListener('visibilitychange', onVisibility)
    window.removeEventListener('pagehide', onPageHide)
  })
}
