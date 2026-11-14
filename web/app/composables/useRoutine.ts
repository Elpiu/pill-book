import { db, getSetting } from '~/db'
import { reminderIcs, googleCalendarUrl, type ReminderEvent } from '~/utils/calendar'
import {
  computeStreak,
  dayKey,
  DEFAULT_TIME,
  emptyActivity,
  goalMinutesOf,
  plural,
  REMINDER_DAYS,
  reminderEnd,
  reminderStart,
  reminderState,
  type ActivityRecord,
  type RoutineSettings,
} from '~/utils/routine'

/** Il messaggio di quando, leggendo, si raggiunge l'obiettivo del giorno: il registro lo segnala una volta. */
export function useGoalCelebration() {
  const toast = useToast()
  return async () => {
    const streak = computeStreak(await db.activity.toArray(), new Date())
    toast.add({
      title: 'Obiettivo di oggi raggiunto',
      description: `${plural(streak.current, 'giorno', 'giorni')} di fila`,
      icon: 'i-lucide-flame',
      color: 'success',
    })
  }
}

/** Routine e registro delle giornate, aggiornati da soli quando cambiano nel database. */
export function useRoutine() {
  const { app } = useRuntimeConfig()
  const { data, loaded } = useLiveQuery(async () => {
    const [records, routine] = await Promise.all([
      db.activity.toArray(),
      getSetting<Partial<RoutineSettings>>('routine'),
    ])
    return { records, routine: routine ?? {} }
  })

  // Si ricalcola anche a mezzanotte, alla prima lettura del giorno dopo
  const now = ref(new Date())
  const clock = setInterval(() => (now.value = new Date()), 60_000)
  onScopeDispose(() => clearInterval(clock))

  const records = computed<ActivityRecord[]>(() => data.value?.records ?? [])
  const routine = computed<Partial<RoutineSettings>>(() => data.value?.routine ?? {})
  /** L'utente ha scelto almeno l'obiettivo: finché no, vale quello predefinito. */
  const configured = computed(() => typeof routine.value.goalMinutes === 'number')
  const goalMinutes = computed(() => goalMinutesOf(routine.value))
  const time = computed(() => routine.value.time ?? DEFAULT_TIME)
  const today = computed(() => {
    const key = dayKey(now.value)
    return records.value.find(record => record.day === key) ?? emptyActivity(key)
  })
  const streak = computed(() => computeStreak(records.value, now.value))
  const reminder = computed(() => reminderState(routine.value, records.value, now.value))

  /** Lettura e scrittura in una transazione: due salvataggi ravvicinati non si cancellano a vicenda. */
  async function save(changes: Partial<RoutineSettings>) {
    await db.transaction('rw', db.settings, async () => {
      const current = ((await db.settings.get('routine'))?.value ?? {}) as Partial<RoutineSettings>
      await db.settings.put({ key: 'routine', value: { goalMinutes: goalMinutesOf(current), ...current, ...changes } })
    })
  }

  /**
   * Prepara una serie di promemoria e la segna come aggiunta. Il rinnovo parte dopo la scadenza
   * di quella attiva; una serie nuova parte da oggi o da domani. È sincrona: il link va aperto
   * nello stesso tocco, o il browser blocca la finestra.
   */
  function addReminder(renew = false) {
    const start = reminderStart(routine.value, new Date(), renew)
    const minutes = goalMinutes.value
    const anchor = routine.value.anchor?.trim()
    const url = new URL(app.baseURL, window.location.origin).toString()
    const event: ReminderEvent = {
      startDay: start,
      time: time.value,
      minutes,
      days: REMINDER_DAYS,
      title: `Bookpack: ${minutes} minuti di lettura`,
      description: [anchor ? `${anchor[0]!.toUpperCase()}${anchor.slice(1)}.` : '', `Apri Bookpack: ${url}`]
        .filter(Boolean)
        .join(' '),
      url,
    }
    save({ time: time.value, reminderUntil: reminderEnd(start), reminderTime: time.value }).catch((cause) => {
      console.error('Promemoria non salvato', cause)
    })
    return {
      ics: reminderIcs(event),
      google: googleCalendarUrl(event, Intl.DateTimeFormat().resolvedOptions().timeZone),
      until: reminderEnd(start),
    }
  }

  return { loaded, records, routine, configured, goalMinutes, time, today, streak, reminder, now, save, addReminder }
}
