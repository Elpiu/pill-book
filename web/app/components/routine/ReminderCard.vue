<script setup lang="ts">
import type { useRoutine } from '~/composables/useRoutine'
import { isAppleMobile } from '~/utils/calendar'
import { parseDay, REMINDER_DAYS, RENEW_WINDOW_DAYS } from '~/utils/routine'

const props = defineProps<{ routine: ReturnType<typeof useRoutine> }>()

const apple = ref(false)
onMounted(() => {
  apple.value = isAppleMobile(navigator.userAgent, navigator.platform, navigator.maxTouchPoints)
})

const state = computed(() => props.routine.reminder.value)
const until = computed(() =>
  state.value.kind === 'none'
    ? ''
    : parseDay(state.value.until).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' }),
)

/** Su iPhone il file si apre in Safari, che propone di aggiungerlo; altrove si scarica. */
function openIcs(ics: string) {
  const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }))
  if (apple.value) {
    window.open(url, '_blank')
  }
  else {
    const link = document.createElement('a')
    link.href = url
    link.download = 'bookpack-routine.ics'
    link.click()
  }
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

/** Tutto nello stesso tocco: aperto dopo un'attesa, il link verrebbe bloccato. */
function add(way: 'ics' | 'google', renew = false) {
  const prepared = props.routine.addReminder(renew)
  if (way === 'google') window.open(prepared.google, '_blank', 'noopener')
  else openIcs(prepared.ics)
}

const primary = computed(() => (apple.value ? 'ics' : 'google'))
const secondary = computed(() => (apple.value ? 'google' : 'ics'))
const labels = { ics: 'Aggiungi al calendario', google: 'Aggiungi a Google Calendar' }
const alternatives = { ics: 'Usa invece il file .ics', google: 'Usa invece Google Calendar' }
</script>

<template>
  <section
    class="space-y-3"
    data-testid="reminder-card"
  >
    <h2 class="font-semibold">
      Promemoria
    </h2>

    <template v-if="state.kind !== 'active'">
      <p class="text-sm text-muted">
        <template v-if="state.kind === 'expired'">
          Il promemoria è scaduto {{ until }}.
        </template>
        Un evento ogni giorno alle {{ routine.time.value }} nel calendario del telefono, per {{ REMINDER_DAYS }} giorni: poi si spegne da solo, così se smetti di usare l'app non ricevi più nulla.
      </p>
      <div class="flex flex-wrap items-center gap-3">
        <UButton
          icon="i-lucide-calendar-plus"
          :label="labels[primary]"
          @click="add(primary)"
        />
        <UButton
          color="neutral"
          variant="link"
          :label="alternatives[secondary]"
          @click="add(secondary)"
        />
      </div>
    </template>

    <template v-else>
      <p
        class="text-sm"
        data-testid="reminder-until"
      >
        Promemoria attivo fino a {{ until }}.
      </p>

      <UAlert
        v-if="state.timeChanged"
        color="warning"
        variant="subtle"
        icon="i-lucide-clock"
        title="Hai cambiato orario"
        :description="`Aggiungi il promemoria delle ${routine.time.value} e cancella dal calendario il vecchio evento Bookpack, che resta all'orario precedente.`"
      >
        <template #actions>
          <UButton
            size="sm"
            :label="labels[primary]"
            @click="add(primary)"
          />
        </template>
      </UAlert>

      <div
        v-else-if="state.daysLeft < RENEW_WINDOW_DAYS"
        class="flex flex-wrap items-center gap-3"
      >
        <UButton
          icon="i-lucide-calendar-sync"
          :label="`Rinnova per altri ${REMINDER_DAYS} giorni`"
          @click="add(primary, true)"
        />
        <UButton
          color="neutral"
          variant="link"
          :label="alternatives[secondary]"
          @click="add(secondary, true)"
        />
      </div>

      <p class="text-sm text-muted">
        Per toglierlo prima: apri l'evento «Bookpack» nel calendario e scegli di eliminare tutti gli eventi futuri. L'app non può farlo da sola.
      </p>
    </template>
  </section>
</template>
