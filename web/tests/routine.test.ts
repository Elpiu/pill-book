import { describe, expect, it } from 'vitest'
import {
  addDays,
  applyActivity,
  calendarWeeks,
  computeStreak,
  minutesLeft,
  todayMessage,
  dayKey,
  emptyActivity,
  goalMinutesOf,
  mergeActivity,
  weekKey,
  type ActivityRecord,
} from '~/utils/routine'

/** Giovedì 12 novembre 2026, a metà pomeriggio. */
const thursday = new Date(2026, 10, 12, 16, 30)

function met(...days: string[]): ActivityRecord[] {
  return days.map(day => ({ ...emptyActivity(day), seconds: 900, met: true }))
}

describe('giorni', () => {
  it('usa la data locale e somma giorni di calendario anche tra mesi e anni', () => {
    expect(dayKey(thursday)).toBe('2026-11-12')
    expect(dayKey(new Date(2026, 10, 12, 23, 59))).toBe('2026-11-12')
    expect(addDays('2026-11-30', 1)).toBe('2026-12-01')
    expect(addDays('2027-01-01', -1)).toBe('2026-12-31')
    // Passaggio all'ora solare in Europa
    expect(addDays('2026-10-24', 2)).toBe('2026-10-26')
  })

  it('la settimana comincia di lunedì', () => {
    expect(weekKey('2026-11-12')).toBe('2026-11-09')
    expect(weekKey('2026-11-09')).toBe('2026-11-09')
    expect(weekKey('2026-11-15')).toBe('2026-11-09')
    expect(weekKey('2026-11-16')).toBe('2026-11-16')
  })
})

describe('registro della giornata', () => {
  it('somma le attività e segna la giornata quando i minuti raggiungono l\'obiettivo', () => {
    let record = emptyActivity('2026-11-12')
    record = applyActivity(record, { seconds: 300, cards: 4 }, 600)
    expect(record).toMatchObject({ seconds: 300, cards: 4, met: false })
    record = applyActivity(record, { seconds: 300, answers: 2, chapters: 1 }, 600)
    expect(record).toMatchObject({ seconds: 600, answers: 2, chapters: 1, met: true })
  })

  it('una giornata riuscita resta tale anche se poi l\'obiettivo cresce', () => {
    const done = applyActivity(emptyActivity('2026-11-12'), { seconds: 300 }, 300)
    expect(applyActivity(done, { cards: 1 }, 1200).met).toBe(true)
  })

  it('obiettivo di 10 minuti finché l\'utente non ne sceglie uno', () => {
    expect(goalMinutesOf(undefined)).toBe(10)
    expect(goalMinutesOf({ goalMinutes: 15 })).toBe(15)
    expect(goalMinutesOf({ goalMinutes: 0 })).toBe(10)
  })

  it('fondendo due export vince il valore più alto di ogni campo', () => {
    const a = { ...emptyActivity('2026-11-12'), seconds: 700, cards: 3, met: true }
    const b = { ...emptyActivity('2026-11-12'), seconds: 400, cards: 9, answers: 2 }
    expect(mergeActivity(a, b)).toEqual({ day: '2026-11-12', seconds: 700, cards: 9, answers: 2, chapters: 0, met: true })
  })
})

describe('streak', () => {
  it('senza giornate riuscite è zero', () => {
    expect(computeStreak([], thursday)).toEqual({ current: 0, best: 0, todayMet: false, freeDayUsed: false })
  })

  it('conta i giorni di fila fino a oggi', () => {
    const streak = computeStreak(met('2026-11-10', '2026-11-11', '2026-11-12'), thursday)
    expect(streak).toMatchObject({ current: 3, todayMet: true, freeDayUsed: false })
  })

  it('oggi non ancora riuscito non interrompe la serie', () => {
    const streak = computeStreak(met('2026-11-10', '2026-11-11'), thursday)
    expect(streak).toMatchObject({ current: 2, todayMet: false, freeDayUsed: false })
  })

  it('un giorno saltato nella settimana è il giorno libero: non interrompe e non conta', () => {
    const streak = computeStreak(met('2026-11-09', '2026-11-11', '2026-11-12'), thursday)
    expect(streak).toMatchObject({ current: 3, freeDayUsed: true })
  })

  it('due giorni saltati nella stessa settimana interrompono la serie', () => {
    const streak = computeStreak(met('2026-11-09', '2026-11-12'), thursday)
    expect(streak.current).toBe(1)
  })

  it('ogni settimana ha il suo giorno libero', () => {
    // Saltati domenica 8 (settimana precedente) e martedì 10 (questa settimana)
    const streak = computeStreak(met('2026-11-06', '2026-11-07', '2026-11-09', '2026-11-11', '2026-11-12'), thursday)
    expect(streak.current).toBe(5)
  })

  it('ieri saltato e oggi ancora da fare: il giorno libero tiene viva la serie', () => {
    const streak = computeStreak(met('2026-11-09', '2026-11-10'), thursday)
    expect(streak).toMatchObject({ current: 2, todayMet: false, freeDayUsed: true })
  })

  it('il record è la serie più lunga, anche se ormai finita', () => {
    const old = met('2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04')
    const streak = computeStreak([...old, ...met('2026-11-12')], thursday)
    expect(streak).toMatchObject({ current: 1, best: 4 })
  })

  it('le giornate con minuti ma senza obiettivo raggiunto non contano', () => {
    const partial = { ...emptyActivity('2026-11-12'), seconds: 120 }
    expect(computeStreak([partial], thursday).current).toBe(0)
  })
})

describe('frase della scheda Oggi', () => {
  const today = (seconds: number) => ({ ...emptyActivity('2026-11-12'), seconds })

  it('obiettivo raggiunto: festeggia la serie', () => {
    const records = met('2026-11-11', '2026-11-12')
    expect(todayMessage(records[1]!, 10, computeStreak(records, thursday), records)).toBe('Obiettivo raggiunto: 2 giorni di fila')
  })

  it('serie in corso: quanti minuti mancano per allungarla', () => {
    const records = [...met('2026-11-10', '2026-11-11'), today(6 * 60 + 30)]
    expect(minutesLeft(today(6 * 60 + 30), 10)).toBe(4)
    expect(todayMessage(today(6 * 60 + 30), 10, computeStreak(records, thursday), records))
      .toBe('Mancano 4 minuti per arrivare a 3 giorni')
    expect(todayMessage(today(9 * 60 + 30), 10, computeStreak(records, thursday), records))
      .toBe('Manca 1 minuto per arrivare a 3 giorni')
  })

  it('dopo una pausa invita a ricominciare, senza parlare di serie perse', () => {
    const records = met('2026-10-01', '2026-10-02')
    const message = todayMessage(today(0), 10, computeStreak(records, thursday), records)
    expect(message).toBe('Ricomincia oggi: bastano 10 minuti')
    expect(message).not.toMatch(/pers/)
  })

  it('primo giorno: invita a cominciare', () => {
    expect(todayMessage(today(0), 5, computeStreak([], thursday), [])).toBe('Leggi 5 minuti per cominciare la tua serie')
  })
})

describe('calendario', () => {
  it('ultime 12 settimane da lunedì, con i giorni futuri segnati e l\'intensità rispetto all\'obiettivo', () => {
    const records = [
      { ...emptyActivity('2026-11-09'), seconds: 120 },
      { ...emptyActivity('2026-11-10'), seconds: 400 },
      { ...emptyActivity('2026-11-11'), seconds: 700, met: true },
      { ...emptyActivity('2026-11-12'), seconds: 1500, met: true },
    ]
    const weeks = calendarWeeks(records, thursday, 10)
    expect(weeks).toHaveLength(12)
    expect(weeks.every(week => week.length === 7)).toBe(true)
    expect(weeks[0]![0]!.day).toBe('2026-08-24')
    const last = weeks.at(-1)!
    expect(last.map(day => day.level)).toEqual([1, 2, 3, 4, 0, 0, 0])
    expect(last.map(day => day.future)).toEqual([false, false, false, false, true, true, true])
  })
})
