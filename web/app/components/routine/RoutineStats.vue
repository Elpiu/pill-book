<script setup lang="ts">
import type { useRoutine } from '~/composables/useRoutine'
import { plural, todayMessage } from '~/utils/routine'

const props = defineProps<{ routine: ReturnType<typeof useRoutine> }>()

const minutes = computed(() => Math.floor(props.routine.today.value.seconds / 60))
const streak = computed(() => props.routine.streak.value)
const message = computed(() =>
  todayMessage(props.routine.today.value, props.routine.goalMinutes.value, streak.value, props.routine.records.value),
)
</script>

<template>
  <section
    class="space-y-3"
    data-testid="routine-stats"
  >
    <p class="font-serif text-lg">
      {{ message }}
    </p>
    <dl class="grid grid-cols-3 gap-2 text-center">
      <div class="rounded-xl bg-elevated p-3">
        <dt class="text-xs text-muted">
          Oggi
        </dt>
        <dd class="text-lg font-semibold tabular-nums">
          {{ minutes }}/{{ routine.goalMinutes.value }} min
        </dd>
      </div>
      <div class="rounded-xl bg-elevated p-3">
        <dt class="text-xs text-muted">
          Di fila
        </dt>
        <dd class="text-lg font-semibold tabular-nums">
          {{ plural(streak.current, 'giorno', 'giorni') }}
        </dd>
      </div>
      <div class="rounded-xl bg-elevated p-3">
        <dt class="text-xs text-muted">
          Record
        </dt>
        <dd class="text-lg font-semibold tabular-nums">
          {{ plural(streak.best, 'giorno', 'giorni') }}
        </dd>
      </div>
    </dl>
    <p class="text-sm text-muted">
      <template v-if="streak.freeDayUsed">
        Il giorno libero di questa settimana l'hai già usato: da qui alla domenica ogni giorno conta.
      </template>
      <template v-else>
        Ogni settimana un giorno saltato non interrompe la serie.
      </template>
    </p>
  </section>
</template>
