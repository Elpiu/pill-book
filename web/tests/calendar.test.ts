import { describe, expect, it } from 'vitest'
import { googleCalendarUrl, isAppleMobile, reminderIcs, type ReminderEvent } from '~/utils/calendar'
import { reminderEnd, reminderStart, reminderState, emptyActivity } from '~/utils/routine'

const event: ReminderEvent = {
  startDay: '2026-11-15',
  time: '08:00',
  minutes: 10,
  days: 30,
  title: 'Bookpack: 10 minuti di lettura',
  description: 'Dopo il caffè, con calma; poi apri Bookpack: https://elpiu.github.io/pill-book/',
  url: 'https://elpiu.github.io/pill-book/',
}

describe('file .ics', () => {
  const ics = reminderIcs(event, new Date(Date.UTC(2026, 10, 14, 20, 30)))
  const unfolded = ics.replace(/\r\n /g, '')

  it('usa righe CRLF e chiude il calendario', () => {
    expect(ics.endsWith('END:VCALENDAR\r\n')).toBe(true)
    expect(ics.replace(/\r\n/g, '')).not.toContain('\n')
  })

  it('ripete ogni giorno per 30 giorni all\'ora locale scelta, con un avviso all\'inizio', () => {
    expect(unfolded).toContain('DTSTART:20261115T080000\r\n')
    expect(unfolded).toContain('DURATION:PT10M\r\n')
    expect(unfolded).toContain('RRULE:FREQ=DAILY;COUNT=30\r\n')
    expect(unfolded).toContain('TRIGGER:PT0M\r\n')
    expect(unfolded).toContain('DTSTAMP:20261114T203000Z\r\n')
    expect(unfolded).toContain('UID:routine-2026-11-15-0800@bookpack\r\n')
  })

  it('protegge virgole e punti e virgola nel testo', () => {
    expect(unfolded).toContain('DESCRIPTION:Dopo il caffè\\, con calma\\; poi apri Bookpack')
  })

  it('ripiega le righe oltre 75 byte, contando gli accenti come due byte', () => {
    const encoder = new TextEncoder()
    for (const line of ics.split('\r\n')) expect(encoder.encode(line).length).toBeLessThanOrEqual(75)
    expect(ics).toContain('\r\n ')
  })
})

describe('link a Google Calendar', () => {
  it('compila titolo, orari, ricorrenza e fuso', () => {
    const url = new URL(googleCalendarUrl(event, 'Europe/Rome'))
    expect(url.origin + url.pathname).toBe('https://calendar.google.com/calendar/render')
    expect(url.searchParams.get('action')).toBe('TEMPLATE')
    expect(url.searchParams.get('text')).toBe(event.title)
    expect(url.searchParams.get('dates')).toBe('20261115T080000/20261115T081000')
    expect(url.searchParams.get('recur')).toBe('RRULE:FREQ=DAILY;COUNT=30')
    expect(url.searchParams.get('ctz')).toBe('Europe/Rome')
  })

  it('un evento vicino a mezzanotte finisce il giorno dopo', () => {
    const url = new URL(googleCalendarUrl({ ...event, time: '23:55' }))
    expect(url.searchParams.get('dates')).toBe('20261115T235500/20261116T000500')
  })
})

describe('dispositivo', () => {
  it('riconosce iPhone e iPad, anche quelli che si presentano come Mac', () => {
    expect(isAppleMobile('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)')).toBe(true)
    expect(isAppleMobile('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'MacIntel', 5)).toBe(true)
    expect(isAppleMobile('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'MacIntel', 0)).toBe(false)
    expect(isAppleMobile('Mozilla/5.0 (Linux; Android 15; Pixel 9)')).toBe(false)
  })
})

describe('scadenza e rinnovo del promemoria', () => {
  const morning = new Date(2026, 10, 14, 7, 0)
  const evening = new Date(2026, 10, 14, 21, 0)

  it('una serie nuova parte oggi, o domani se l\'orario è passato, e dura 30 giorni', () => {
    expect(reminderStart({ time: '08:00' }, morning)).toBe('2026-11-14')
    expect(reminderStart({ time: '08:00' }, evening)).toBe('2026-11-15')
    expect(reminderEnd('2026-11-15')).toBe('2026-12-14')
  })

  it('un rinnovo parte dopo la scadenza, così le due serie non si sovrappongono', () => {
    expect(reminderStart({ time: '08:00', reminderUntil: '2026-11-18' }, evening, true)).toBe('2026-11-19')
    // Un cambio di orario invece parte subito: il vecchio evento va cancellato
    expect(reminderStart({ time: '08:00', reminderUntil: '2026-11-18' }, evening)).toBe('2026-11-15')
  })

  it('propone il rinnovo nell\'ultima settimana solo a chi ha letto negli ultimi 3 giorni', () => {
    const recent = [{ ...emptyActivity('2026-11-13'), seconds: 300 }]
    const old = [{ ...emptyActivity('2026-11-05'), seconds: 300 }]
    const routine = { time: '08:00', reminderTime: '08:00', reminderUntil: '2026-11-18' }
    expect(reminderState(routine, recent, evening)).toMatchObject({ kind: 'active', daysLeft: 4, renewable: true })
    expect(reminderState(routine, old, evening)).toMatchObject({ kind: 'active', renewable: false })
    expect(reminderState({ ...routine, reminderUntil: '2026-12-10' }, recent, evening)).toMatchObject({ renewable: false })
  })

  it('segnala un cambio di orario e una serie scaduta', () => {
    const routine = { time: '21:00', reminderTime: '08:00', reminderUntil: '2026-12-10' }
    expect(reminderState(routine, [], evening)).toMatchObject({ kind: 'active', timeChanged: true })
    expect(reminderState({ reminderUntil: '2026-11-10' }, [], evening)).toEqual({ kind: 'expired', until: '2026-11-10' })
    expect(reminderState({}, [], evening)).toEqual({ kind: 'none' })
  })
})
