import { describe, expect, it } from 'vitest'
import { createActiveTimer, FLUSH_EVERY_MS, IDLE_MS, TICK_MS } from '~/composables/useReadingTimer'

function setup(options: { listening?: boolean } = {}) {
  let clock = 0
  const state = { visible: true, listening: options.listening ?? false }
  const flushed: number[] = []
  const timer = createActiveTimer({
    now: () => clock,
    isVisible: () => state.visible,
    isListening: () => state.listening,
    onFlush: seconds => flushed.push(seconds),
  })
  /** Fa passare il tempo a colpi di tick, come l'intervallo vero. */
  const run = (ms: number) => {
    for (let elapsed = 0; elapsed < ms; elapsed += TICK_MS) {
      clock += TICK_MS
      timer.tick()
    }
  }
  const total = () => flushed.reduce((sum, seconds) => sum + seconds, 0)
  return { timer, state, flushed, run, total, advance: (ms: number) => (clock += ms) }
}

describe('minuti di lettura attiva', () => {
  it('conta il tempo con la pagina visibile e salva ogni 30 secondi', () => {
    const { run, flushed } = setup()
    run(60_000)
    expect(flushed).toEqual([30, 30])
    expect(FLUSH_EVERY_MS).toBe(30_000)
  })

  it('smette di contare dopo 3 minuti senza interazioni', () => {
    const { run, timer, total } = setup()
    run(IDLE_MS + 60_000)
    timer.flush()
    expect(total()).toBe(IDLE_MS / 1000)
  })

  it('un\'interazione fa ripartire il conteggio', () => {
    const { run, timer, total } = setup()
    run(IDLE_MS + 60_000)
    timer.interaction()
    run(30_000)
    timer.flush()
    expect(total()).toBe(IDLE_MS / 1000 + 30)
  })

  it('l\'ascolto conta anche senza toccare lo schermo', () => {
    const { run, timer, total } = setup({ listening: true })
    run(10 * 60_000)
    timer.flush()
    expect(total()).toBe(600)
  })

  it('con la pagina nascosta non conta', () => {
    const { run, timer, state, total } = setup()
    state.visible = false
    run(60_000)
    timer.flush()
    expect(total()).toBe(0)
  })

  it('un salto lungo dei timer in background non diventa tempo di lettura', () => {
    const { advance, timer, total } = setup()
    advance(20 * 60_000)
    // Al ritorno l'utente tocca subito: conta solo il tick, non i 20 minuti
    timer.interaction()
    timer.tick()
    timer.flush()
    expect(total()).toBe((TICK_MS * 2) / 1000)
  })

  it('dopo una pausa nascosta riparte da adesso', () => {
    const { advance, timer, total } = setup()
    advance(60_000)
    timer.resume()
    timer.interaction()
    advance(TICK_MS)
    timer.tick()
    timer.flush()
    expect(total()).toBe(TICK_MS / 1000)
  })

  it('salva solo secondi interi e tiene il resto per la volta dopo', () => {
    const { advance, timer, flushed } = setup()
    advance(2500)
    timer.tick()
    timer.flush()
    advance(2500)
    timer.tick()
    timer.flush()
    expect(flushed).toEqual([2, 3])
  })
})
