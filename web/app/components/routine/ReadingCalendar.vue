<script setup lang="ts">
import type { useRoutine } from '~/composables/useRoutine'
import { calendarWeeks, parseDay, plural, type CalendarDay } from '~/utils/routine'

const props = defineProps<{ routine: ReturnType<typeof useRoutine> }>()

const WEEKDAYS = ['L', 'M', 'M', 'G', 'V', 'S', 'D']
const LEVELS = ['bg-(--ui-bg-accented)', 'bg-primary/25', 'bg-primary/50', 'bg-primary/80', 'bg-primary']

const weeks = computed(() =>
  calendarWeeks(props.routine.records.value, props.routine.now.value, props.routine.goalMinutes.value),
)
const selected = ref<string>()
const detail = computed(() => {
  if (!selected.value) return undefined
  const record = props.routine.records.value.find(item => item.day === selected.value)
  const date = parseDay(selected.value).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })
  if (!record?.seconds) return `${date}: nessuna lettura`
  const parts = [
    plural(Math.floor(record.seconds / 60), 'minuto', 'minuti'),
    plural(record.cards, 'card', 'card'),
    plural(record.answers, 'risposta', 'risposte'),
  ]
  if (record.chapters) parts.push(plural(record.chapters, 'capitolo', 'capitoli'))
  return `${date}: ${parts.join(', ')}${record.met ? ', obiettivo raggiunto' : ''}`
})

function label(day: CalendarDay): string {
  const date = parseDay(day.day).toLocaleDateString('it-IT', { day: 'numeric', month: 'long' })
  if (!day.seconds) return `${date}: nessuna lettura`
  return `${date}: ${plural(Math.floor(day.seconds / 60), 'minuto', 'minuti')}${day.met ? ', obiettivo raggiunto' : ''}`
}
</script>

<template>
  <section
    class="space-y-3"
    data-testid="reading-calendar"
  >
    <h2 class="font-semibold">
      Le ultime 12 settimane
    </h2>
    <div class="flex gap-1">
      <div class="grid grid-rows-7 gap-1 pe-1 text-[10px] leading-none text-muted">
        <span
          v-for="(weekday, index) in WEEKDAYS"
          :key="index"
          class="flex h-5 items-center"
        >{{ weekday }}</span>
      </div>
      <div
        v-for="week in weeks"
        :key="week[0]!.day"
        class="grid flex-1 grid-rows-7 gap-1"
      >
        <span
          v-for="day in week"
          :key="day.day"
          class="h-5"
        >
          <button
            v-if="!day.future"
            type="button"
            class="block size-full rounded-sm outline-offset-1"
            :class="[LEVELS[day.level], selected === day.day ? 'outline-2 outline-(--ui-text)' : '']"
            :aria-label="label(day)"
            :aria-pressed="selected === day.day"
            :data-day="day.day"
            @click="selected = selected === day.day ? undefined : day.day"
          />
        </span>
      </div>
    </div>
    <p
      class="min-h-5 text-sm text-muted first-letter:uppercase"
      aria-live="polite"
      data-testid="calendar-detail"
    >
      {{ detail ?? 'Tocca un giorno per vedere cosa hai letto.' }}
    </p>
  </section>
</template>
