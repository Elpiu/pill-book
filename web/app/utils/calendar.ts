/**
 * Promemoria della routine come evento ricorrente: file .ics (RFC 5545) e link a Google Calendar.
 * Niente server: l'evento finisce nel calendario dell'utente e l'app non lo può più toccare, per
 * questo la serie ha un numero fisso di giorni.
 */

export interface ReminderEvent {
  /** Primo giorno, YYYY-MM-DD. */
  startDay: string
  /** HH:MM, ora locale. */
  time: string
  minutes: number
  days: number
  title: string
  description: string
  url: string
}

const MAX_LINE_BYTES = 75

function compact(day: string, time: string): string {
  return `${day.replace(/-/g, '')}T${time.replace(':', '')}00`
}

/** Fine dell'evento: può cadere il giorno dopo, se l'orario è vicino a mezzanotte. */
function endOf(event: ReminderEvent): string {
  const [year, month, date] = event.startDay.split('-').map(Number)
  const [hours, minutes] = event.time.split(':').map(Number)
  const end = new Date(year!, month! - 1, date!, hours!, minutes! + event.minutes)
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${end.getFullYear()}${pad(end.getMonth() + 1)}${pad(end.getDate())}T${pad(end.getHours())}${pad(end.getMinutes())}00`
}

function escapeText(text: string): string {
  return text.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n')
}

/** Le righe oltre 75 byte vanno spezzate, e le continuazioni cominciano con uno spazio. */
function fold(line: string): string {
  const encoder = new TextEncoder()
  const parts: string[] = []
  let current = ''
  let bytes = 0
  for (const char of line) {
    const size = encoder.encode(char).length
    const limit = parts.length ? MAX_LINE_BYTES - 1 : MAX_LINE_BYTES
    if (bytes + size > limit) {
      parts.push(current)
      current = ''
      bytes = 0
    }
    current += char
    bytes += size
  }
  parts.push(current)
  return parts.join('\r\n ')
}

function utcStamp(date: Date): string {
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

export function reminderIcs(event: ReminderEvent, now = new Date()): string {
  const summary = escapeText(event.title)
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Bookpack//Routine di lettura//IT',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:routine-${event.startDay}-${event.time.replace(':', '')}@bookpack`,
    `DTSTAMP:${utcStamp(now)}`,
    // Ora locale senza fuso: il calendario la mostra sempre all'orario scelto
    `DTSTART:${compact(event.startDay, event.time)}`,
    `DURATION:PT${event.minutes}M`,
    `RRULE:FREQ=DAILY;COUNT=${event.days}`,
    `SUMMARY:${summary}`,
    `DESCRIPTION:${escapeText(event.description)}`,
    `URL:${event.url}`,
    'BEGIN:VALARM',
    'ACTION:DISPLAY',
    `DESCRIPTION:${summary}`,
    'TRIGGER:PT0M',
    'END:VALARM',
    'END:VEVENT',
    'END:VCALENDAR',
  ]
  return lines.map(fold).join('\r\n') + '\r\n'
}

/** iPhone e iPad, anche gli iPad che si presentano come Mac: lì il file .ics apre il calendario. */
export function isAppleMobile(userAgent: string, platform = '', maxTouchPoints = 0): boolean {
  return /iPhone|iPad|iPod/.test(userAgent) || (platform === 'MacIntel' && maxTouchPoints > 1)
}

/** Link all'editor di Google Calendar con l'evento compilato. Il formato non è documentato. */
export function googleCalendarUrl(event: ReminderEvent, timeZone?: string): string {
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title,
    dates: `${compact(event.startDay, event.time)}/${endOf(event)}`,
    details: event.description,
    recur: `RRULE:FREQ=DAILY;COUNT=${event.days}`,
  })
  if (timeZone) params.set('ctz', timeZone)
  return `https://calendar.google.com/calendar/render?${params.toString()}`
}
