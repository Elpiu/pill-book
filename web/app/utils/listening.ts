import type { Card } from '~/types/bookpack'
import { splitSentences, type SpeechItem } from './speech'

/**
 * Cosa si legge di card e riassunto in modalità ascolto. Solo testo del libro, nella sua lingua:
 * nessuna parola dell'interfaccia, i passaggi si segnano con pause.
 */
export const TITLE_PAUSE_MS = 400
export const STEP_PAUSE_MS = 700
export const SECTION_PAUSE_MS = 1500
/** Tempo per pensare alla risposta di una domanda, saltabile con un tocco. */
export const THINK_MS = 7000
/** Segna l'inizio della risposta di una domanda: la sessione la mostra sulla card. */
export const ANSWER_TAG = 'answer'

function say(text: string | null | undefined, lang: string, tag?: string): SpeechItem[] {
  // I backtick dei comandi nei passi non vanno pronunciati
  const sentences = splitSentences((text ?? '').replace(/`/g, ''), lang)
  return sentences.map((sentence, index) =>
    index === 0 && tag ? { kind: 'say', text: sentence, tag } : { kind: 'say', text: sentence },
  )
}

function pause(ms: number): SpeechItem {
  return { kind: 'pause', ms }
}

function titled(card: Card, lang: string): SpeechItem[] {
  const title = say(card.title, lang)
  return title.length ? [...title, pause(TITLE_PAUSE_MS)] : []
}

/** Frasi e pause di una card. Il codice resta sullo schermo e non viene letto. */
export function cardScript(card: Card, lang: string): SpeechItem[] {
  switch (card.type) {
    case 'check':
      return [
        ...say(card.body, lang),
        { kind: 'pause', ms: THINK_MS, think: true },
        ...say(card.answer, lang, ANSWER_TAG),
      ]
    case 'procedure':
      return [
        ...titled(card, lang),
        ...say(card.body, lang),
        ...(card.steps ?? []).flatMap(step => [pause(STEP_PAUSE_MS), ...say(step, lang)]),
      ]
    case 'section':
      return [...titled(card, lang), ...say(card.body, lang), pause(SECTION_PAUSE_MS)]
    case 'quote':
      return say(card.body, lang)
    default:
      return [...titled(card, lang), ...say(card.body, lang), ...say(card.details, lang)]
  }
}

export function summaryScript(summary: string, lang: string): SpeechItem[] {
  return summary
    .split(/\n\s*\n/)
    .flatMap((paragraph, index) => [...(index ? [pause(TITLE_PAUSE_MS)] : []), ...say(paragraph, lang)])
}
