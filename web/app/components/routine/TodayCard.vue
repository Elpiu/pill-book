<script setup lang="ts">
import { parseDay, plural, todayMessage } from '~/utils/routine'

const routine = useRoutine()
const { today, goalMinutes, streak, reminder, records, configured, loaded } = routine

const RADIUS = 26
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

const minutes = computed(() => Math.floor(today.value.seconds / 60))
const progress = computed(() => Math.min(1, today.value.seconds / (goalMinutes.value * 60)))
const message = computed(() => todayMessage(today.value, goalMinutes.value, streak.value, records.value))
const renewal = computed(() => {
  const state = reminder.value
  if (state.kind !== 'active' || !state.renewable) return ''
  const day = parseDay(state.until).toLocaleDateString('it-IT', { weekday: 'long' })
  return `Il promemoria scade ${day}: rinnovalo`
})
</script>

<template>
  <NuxtLink
    v-if="loaded"
    to="/routine"
    class="flex items-center gap-4 rounded-2xl border border-default p-4 transition hover:bg-elevated/50 focus-visible:outline-2 focus-visible:outline-primary"
    data-testid="today-card"
  >
    <span class="relative size-16 shrink-0">
      <svg
        viewBox="0 0 64 64"
        class="size-16 -rotate-90"
        aria-hidden="true"
      >
        <circle
          cx="32"
          cy="32"
          :r="RADIUS"
          fill="none"
          stroke-width="6"
          class="stroke-(--ui-bg-accented)"
        />
        <circle
          cx="32"
          cy="32"
          :r="RADIUS"
          fill="none"
          stroke-width="6"
          stroke-linecap="round"
          class="stroke-(--ui-primary) transition-[stroke-dashoffset] duration-500"
          :stroke-dasharray="CIRCUMFERENCE"
          :stroke-dashoffset="CIRCUMFERENCE * (1 - progress)"
        />
      </svg>
      <span class="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span class="text-base font-semibold tabular-nums">{{ minutes }}</span>
        <span class="text-[10px] text-muted">/ {{ goalMinutes }} min</span>
      </span>
    </span>

    <span class="min-w-0 flex-1">
      <span class="flex items-center gap-2 text-sm font-semibold">
        Oggi
        <span
          v-if="streak.current"
          class="flex items-center gap-1 text-primary"
          :aria-label="`Serie di ${plural(streak.current, 'giorno', 'giorni')}`"
        >
          <UIcon
            name="i-lucide-flame"
            class="size-4"
            aria-hidden="true"
          />
          {{ streak.current }}
        </span>
      </span>
      <span
        class="mt-0.5 block text-sm"
        data-testid="today-message"
      >{{ message }}</span>
      <span
        v-if="!configured"
        class="mt-1 block text-sm font-medium text-primary"
      >Scegli il tuo obiettivo</span>
      <span
        v-else-if="renewal"
        class="mt-1 block text-sm font-medium text-primary"
      >{{ renewal }}</span>
    </span>

    <UIcon
      name="i-lucide-chevron-right"
      class="size-5 shrink-0 text-muted"
      aria-hidden="true"
    />
  </NuxtLink>
</template>
