/**
 * Routine di lettura: registro per giorno, obiettivo in minuti e streak. Logica pura, i giorni sono
 * date locali del dispositivo nel formato YYYY-MM-DD.
 */

export const GOAL_OPTIONS = [5, 10, 15, 20]
export const DEFAULT_GOAL_MINUTES = 10

/** Una riga per giorno. `met` diventa vero quando i minuti raggiungono l'obiettivo e ci resta. */
export interface ActivityRecord {
  day: string
  seconds: number
  cards: number
  answers: number
  chapters: number
  met: boolean
}

export type ActivityDelta = Partial<Pick<ActivityRecord, 'seconds' | 'cards' | 'answers' | 'chapters'>>

export interface RoutineSettings {
  goalMinutes: number
  /** HH:MM, ora locale. */
  time?: string
  /** Il momento a cui agganciare la lettura, per esempio "dopo il caffè". */
  anchor?: string
  /** Ultimo giorno del promemoria nel calendario, YYYY-MM-DD. */
  reminderUntil?: string
  /** Orario del promemoria aggiunto: se la routine cambia orario, il vecchio evento resta. */
  reminderTime?: string
}

export const DEFAULT_TIME = '08:00'
/** Giorni di una serie di promemoria: poi si spegne da sola, se l'app non si usa più. */
export const REMINDER_DAYS = 30
/** Da quanti giorni prima della scadenza si propone il rinnovo. */
export const RENEW_WINDOW_DAYS = 7
/** Il rinnovo si propone solo a chi ha letto di recente. */
export const RECENT_DAYS = 3

export type ReminderState =
  | { kind: 'none' }
  | { kind: 'expired', until: string }
  | { kind: 'active', until: string, daysLeft: number, renewable: boolean, timeChanged: boolean }

export interface StreakInfo {
  current: number
  best: number
  todayMet: boolean
  /** Il giorno libero di questa settimana è già servito a tenere viva la serie. */
  freeDayUsed: boolean
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

export function dayKey(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function parseDay(day: string): Date {
  const [year, month, date] = day.split('-').map(Number)
  return new Date(year!, month! - 1, date!)
}

/** Somma giorni di calendario: con l'ora legale un giorno non dura sempre 24 ore. */
export function addDays(day: string, amount: number): string {
  const date = parseDay(day)
  date.setDate(date.getDate() + amount)
  return dayKey(date)
}

/** Il lunedì della settimana del giorno: le settimane vanno da lunedì a domenica. */
export function weekKey(day: string): string {
  const date = parseDay(day)
  return addDays(day, -((date.getDay() + 6) % 7))
}

export function goalMinutesOf(routine?: Partial<RoutineSettings>): number {
  const goal = routine?.goalMinutes
  return typeof goal === 'number' && goal > 0 ? goal : DEFAULT_GOAL_MINUTES
}

export function emptyActivity(day: string): ActivityRecord {
  return { day, seconds: 0, cards: 0, answers: 0, chapters: 0, met: false }
}

export function applyActivity(record: ActivityRecord, delta: ActivityDelta, goalSeconds: number): ActivityRecord {
  const next = {
    ...record,
    seconds: record.seconds + (delta.seconds ?? 0),
    cards: record.cards + (delta.cards ?? 0),
    answers: record.answers + (delta.answers ?? 0),
    chapters: record.chapters + (delta.chapters ?? 0),
  }
  return { ...next, met: record.met || next.seconds >= goalSeconds }
}

/** Due registri dello stesso giorno, da due export: vince il valore più alto di ogni campo. */
export function mergeActivity(a: ActivityRecord, b: ActivityRecord): ActivityRecord {
  return {
    day: a.day,
    seconds: Math.max(a.seconds, b.seconds),
    cards: Math.max(a.cards, b.cards),
    answers: Math.max(a.answers, b.answers),
    chapters: Math.max(a.chapters, b.chapters),
    met: a.met || b.met,
  }
}

/**
 * Giornate riuscite consecutive che finiscono in `last`, andando indietro. In ogni settimana un
 * solo giorno non riuscito è coperto come giorno libero: non interrompe e non conta.
 */
function streakEndingAt(met: Set<string>, last: string, first: string): { length: number, freeWeeks: Set<string> } {
  const freeWeeks = new Set<string>()
  let length = 0
  for (let day = last; day >= first; day = addDays(day, -1)) {
    if (met.has(day)) {
      length++
      continue
    }
    const week = weekKey(day)
    if (freeWeeks.has(week)) break
    freeWeeks.add(week)
  }
  return { length, freeWeeks }
}

function daysBetween(from: string, to: string): number {
  return Math.round((parseDay(to).getTime() - parseDay(from).getTime()) / 86_400_000)
}

/**
 * Primo giorno di una nuova serie di promemoria. Un rinnovo parte dopo la scadenza di quella
 * attiva, così non si sovrappongono; una serie nuova, anche per un cambio di orario, parte oggi,
 * o domani se l'orario di oggi è già passato.
 */
export function reminderStart(routine: Partial<RoutineSettings>, now: Date, renew = false): string {
  const today = dayKey(now)
  if (renew && routine.reminderUntil && routine.reminderUntil >= today) return addDays(routine.reminderUntil, 1)
  const [hours, minutes] = (routine.time ?? DEFAULT_TIME).split(':').map(Number)
  const passed = now.getHours() * 60 + now.getMinutes() >= hours! * 60 + minutes!
  return passed ? addDays(today, 1) : today
}

export function reminderEnd(start: string): string {
  return addDays(start, REMINDER_DAYS - 1)
}

export function reminderState(routine: Partial<RoutineSettings>, records: ActivityRecord[], now: Date): ReminderState {
  if (!routine.reminderUntil) return { kind: 'none' }
  const today = dayKey(now)
  if (routine.reminderUntil < today) return { kind: 'expired', until: routine.reminderUntil }
  const daysLeft = daysBetween(today, routine.reminderUntil)
  const since = addDays(today, -(RECENT_DAYS - 1))
  const recent = records.some(record => record.day >= since && record.seconds > 0)
  return {
    kind: 'active',
    until: routine.reminderUntil,
    daysLeft,
    renewable: daysLeft < RENEW_WINDOW_DAYS && recent,
    timeChanged: Boolean(routine.reminderTime && routine.time && routine.reminderTime !== routine.time),
  }
}

export function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`
}

export function minutesLeft(today: ActivityRecord, goalMinutes: number): number {
  return Math.max(0, Math.ceil((goalMinutes * 60 - today.seconds) / 60))
}

/** La frase della scheda Oggi. Dopo una pausa invita a ricominciare, senza ricordare cosa si è perso. */
export function todayMessage(
  today: ActivityRecord,
  goalMinutes: number,
  streak: StreakInfo,
  records: ActivityRecord[],
): string {
  if (streak.todayMet) return `Obiettivo raggiunto: ${plural(streak.current, 'giorno', 'giorni')} di fila`
  const remaining = minutesLeft(today, goalMinutes)
  const left = plural(remaining, 'minuto', 'minuti')
  if (streak.current > 0) return `${remaining === 1 ? 'Manca' : 'Mancano'} ${left} per arrivare a ${streak.current + 1} giorni`
  const readBefore = records.some(record => record.day < today.day && record.seconds > 0)
  if (readBefore) return `Ricomincia oggi: bastano ${plural(goalMinutes, 'minuto', 'minuti')}`
  return `Leggi ${left} per cominciare la tua serie`
}

export interface CalendarDay {
  day: string
  seconds: number
  met: boolean
  /** 0 nessuna lettura, 1 meno di metà obiettivo, 2 almeno metà, 3 riuscita, 4 almeno il doppio. */
  level: 0 | 1 | 2 | 3 | 4
  future: boolean
}

/** Le ultime settimane, dalla più vecchia, ognuna da lunedì a domenica. */
export function calendarWeeks(records: ActivityRecord[], today: Date, goalMinutes: number, weeks = 12): CalendarDay[][] {
  const byDay = new Map(records.map(record => [record.day, record]))
  const todayKey = dayKey(today)
  const goal = goalMinutes * 60
  const first = addDays(weekKey(todayKey), -7 * (weeks - 1))
  return Array.from({ length: weeks }, (_, week) =>
    Array.from({ length: 7 }, (_, weekday): CalendarDay => {
      const day = addDays(first, week * 7 + weekday)
      const record = byDay.get(day)
      const seconds = record?.seconds ?? 0
      const met = Boolean(record?.met)
      const level = !seconds ? 0 : seconds >= goal * 2 ? 4 : met ? 3 : seconds >= goal / 2 ? 2 : 1
      return { day, seconds, met, level, future: day > todayKey }
    }),
  )
}

export function computeStreak(records: ActivityRecord[], today: Date): StreakInfo {
  const met = new Set(records.filter(record => record.met).map(record => record.day))
  const todayKey = dayKey(today)
  const todayMet = met.has(todayKey)
  if (!met.size) return { current: 0, best: 0, todayMet, freeDayUsed: false }

  const first = [...met].sort()[0]!
  // Oggi non è ancora finito: se non è riuscito si parte da ieri, senza consumare il giorno libero
  const last = todayMet ? todayKey : addDays(todayKey, -1)
  const current = streakEndingAt(met, last, first)
  const best = Math.max(
    current.length,
    ...[...met].map(day => streakEndingAt(met, day, first).length),
  )
  return {
    current: current.length,
    best,
    todayMet,
    freeDayUsed: current.length > 0 && current.freeWeeks.has(weekKey(todayKey)),
  }
}
