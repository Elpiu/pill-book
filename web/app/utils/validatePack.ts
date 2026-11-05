import Ajv2020, { type ErrorObject } from 'ajv/dist/2020'
import schema from '#schema'
import type { BookPack } from '~/types/bookpack'

export const SUPPORTED_SCHEMA_VERSION = 1
const MAX_MESSAGES = 8

export type PackValidation =
  | { ok: true, pack: BookPack }
  | { ok: false, errors: string[] }

const ajv = new Ajv2020({ allErrors: true, strict: false })
const validateSchema = ajv.compile(schema)

const SECTION_LABELS: Record<string, string> = {
  chapters: 'capitolo',
  cards: 'card',
  flashcards: 'flashcard',
  glossary: 'voce di glossario',
}

function describePath(instancePath: string): string {
  const parts = instancePath.split('/').filter(Boolean)
  const labels: string[] = []
  parts.forEach((part, i) => {
    if (/^\d+$/.test(part)) return
    const next = parts[i + 1]
    if (next && /^\d+$/.test(next)) {
      labels.push(`${SECTION_LABELS[part] ?? part} ${Number(next) + 1}`)
    }
    else {
      labels.push(part)
    }
  })
  return labels.join(' › ') || 'radice del file'
}

function describeError(error: ErrorObject): string {
  const where = describePath(error.instancePath)
  const params = error.params as Record<string, unknown>
  switch (error.keyword) {
    case 'required': return `${where}: manca il campo "${params.missingProperty}"`
    case 'additionalProperties': return `${where}: campo non previsto "${params.additionalProperty}"`
    case 'minItems': return `${where}: servono almeno ${params.limit} elementi`
    case 'maxItems': return `${where}: al massimo ${params.limit} elementi`
    case 'minLength': return `${where}: non può essere vuoto`
    case 'minimum': return `${where}: deve essere almeno ${params.limit}`
    case 'pattern': return `${where}: formato non valido`
    case 'enum': return `${where}: valore non ammesso`
    case 'type': return `${where}: tipo non valido (atteso ${params.type})`
    default: return `${where}: ${error.message}`
  }
}

function summarize(errors: ErrorObject[]): string[] {
  // I campi nullabili producono un errore per ramo di anyOf: basta il primo per percorso
  const seen = new Set<string>()
  const messages: string[] = []
  for (const error of errors) {
    if (error.keyword === 'anyOf') continue
    const key = `${error.instancePath}|${error.keyword}|${JSON.stringify(error.params)}`
    if (seen.has(key) || seen.has(error.instancePath)) continue
    seen.add(key)
    seen.add(error.instancePath)
    messages.push(describeError(error))
  }
  if (messages.length > MAX_MESSAGES) {
    const hidden = messages.length - MAX_MESSAGES
    return [...messages.slice(0, MAX_MESSAGES), `e altri ${hidden} problemi`]
  }
  return messages
}

function findDuplicateIds(pack: BookPack): string[] {
  const seen = new Set<string>()
  const duplicates = new Set<string>()
  for (const chapter of pack.chapters) {
    const ids = [chapter.id, ...chapter.cards.map(c => c.id), ...chapter.flashcards.map(f => f.id)]
    for (const id of ids) {
      if (seen.has(id)) duplicates.add(id)
      seen.add(id)
    }
  }
  return [...duplicates]
}

export function validatePack(data: unknown): PackValidation {
  if (typeof data !== 'object' || data === null || Array.isArray(data) || !('schemaVersion' in data)) {
    return { ok: false, errors: ['Il file non sembra un book pack: manca "schemaVersion".'] }
  }
  const version = (data as { schemaVersion: unknown }).schemaVersion
  if (version !== SUPPORTED_SCHEMA_VERSION) {
    return {
      ok: false,
      errors: [
        typeof version === 'number' && version > SUPPORTED_SCHEMA_VERSION
          ? `Questo pack usa il formato v${version}, ma l'app arriva alla v${SUPPORTED_SCHEMA_VERSION}. Aggiorna l'app e riprova.`
          : `Formato del pack non supportato (versione ${JSON.stringify(version)}). Rigeneralo con il generatore.`,
      ],
    }
  }
  if (!validateSchema(data)) {
    return { ok: false, errors: summarize(validateSchema.errors ?? []) }
  }
  const pack = data as unknown as BookPack
  const duplicates = findDuplicateIds(pack)
  if (duplicates.length) {
    return { ok: false, errors: [`Id duplicati nel pack: ${duplicates.join(', ')}`] }
  }
  return { ok: true, pack }
}

export function parseAndValidatePack(text: string): PackValidation {
  let data: unknown
  try {
    data = JSON.parse(text)
  }
  catch {
    return { ok: false, errors: ['Il file non è un JSON valido.'] }
  }
  return validatePack(data)
}

export function totalMinutes(pack: BookPack): number {
  return pack.chapters.reduce((sum, chapter) => sum + chapter.estMinutes, 0)
}
