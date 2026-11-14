---
type: C4 Component
title: Promemoria nel calendario
status: stable
groma:
  id: promemoria
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/utils/calendar.ts
    - scanner: vue
      file: web/app/utils/calendar.ts
    - scanner: vue
      file: web/app/components/routine/ReminderCard.vue
  technology: iCalendar (RFC 5545)
  group: Routine
description: 'Evento ricorrente per 30 giorni: file .ics su iPhone, link a Google Calendar altrove.'
---

Senza server l'app non può mandare notifiche né cancellare eventi già nel calendario: per questo la serie scade da sola. Propone il rinnovo nell'ultima settimana, con una serie che parte dopo la scadenza, e avvisa quando l'orario della routine cambia.
