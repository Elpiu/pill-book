import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { SAMPLES } from '~/utils/samples'
import { parseAndValidatePack, totalMinutes, validatePack } from '~/utils/validatePack'

function loadJson(relative: string) {
  return JSON.parse(readFileSync(new URL(relative, import.meta.url), 'utf-8'))
}

const sample = () => loadJson('../../samples/sample.bookpack.json')

describe('validatePack', () => {
  it('accetta i pack d\'esempio', () => {
    expect(validatePack(sample()).ok).toBe(true)
    const full = validatePack(loadJson('../public/samples/how-to-live-on-24-hours-a-day.bookpack.json'))
    expect(full.ok).toBe(true)
    if (full.ok) {
      expect(full.pack.chapters).toHaveLength(12)
      expect(totalMinutes(full.pack)).toBeGreaterThan(12)
    }
  })

  it('il libro d\'esempio esiste in italiano e in inglese, come libri distinti', () => {
    const results = SAMPLES.map(sample => validatePack(loadJson(`../public/samples/${sample.file}`)))
    const packs = results.map(result => (result.ok ? result.pack : undefined))
    expect(packs.every(Boolean)).toBe(true)
    expect(packs.map(pack => pack?.book.lang)).toEqual(['it', 'en'])
    expect(new Set(packs.map(pack => pack?.book.id)).size).toBe(SAMPLES.length)
    expect(packs[1]?.chapters).toHaveLength(12)
  })

  it('rifiuta un file che non è un pack', () => {
    const result = validatePack({ foo: 1 })
    expect(result).toEqual({ ok: false, errors: [expect.stringContaining('schemaVersion')] })
    expect(validatePack([]).ok).toBe(false)
  })

  it('spiega che un pack vecchio va rigenerato', () => {
    const result = validatePack({ ...sample(), schemaVersion: 1 })
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.errors[0]).toContain('Rigeneralo')
  })

  it('spiega che una versione futura richiede di aggiornare l\'app', () => {
    const result = validatePack({ ...sample(), schemaVersion: 3 })
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.errors[0]).toContain('Aggiorna l\'app')
  })

  it('segnala JSON non valido', () => {
    expect(parseAndValidatePack('{ nope')).toEqual({ ok: false, errors: ['Il file non è un JSON valido.'] })
  })

  it('dà errori comprensibili con il percorso del problema', () => {
    const pack = sample()
    pack.chapters[0].cards = pack.chapters[0].cards.slice(0, 2)
    delete pack.book.title
    const result = validatePack(pack)
    expect(result.ok).toBe(false)
    if (result.ok) return
    expect(result.errors).toContain('capitolo 1 › cards: servono almeno 3 elementi')
    expect(result.errors).toContain('book: manca il campo "title"')
  })

  it('rifiuta id duplicati', () => {
    const pack = sample()
    pack.chapters[0].cards[1].id = pack.chapters[0].cards[0].id
    const result = validatePack(pack)
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.errors[0]).toContain('duplicati')
  })

  it('limita il numero di messaggi', () => {
    const pack = sample()
    pack.chapters[0].cards = pack.chapters[0].cards.map((card: object) => ({ ...card, body: '', extra: 1 }))
    pack.chapters[1].cards = pack.chapters[1].cards.map((card: object) => ({ ...card, body: '', extra: 1 }))
    const result = validatePack(pack)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.errors.length).toBeLessThanOrEqual(9)
      expect(result.errors.at(-1)).toMatch(/altri \d+ problemi/)
    }
  })
})
