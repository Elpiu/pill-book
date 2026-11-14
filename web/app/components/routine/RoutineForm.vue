<script setup lang="ts">
import type { useRoutine } from '~/composables/useRoutine'
import { GOAL_OPTIONS } from '~/utils/routine'

const props = defineProps<{ routine: ReturnType<typeof useRoutine> }>()

const ANCHORS = ['Dopo il caffè', 'In treno', 'In pausa pranzo', 'Prima di dormire']

const time = ref(props.routine.time.value)
const anchor = ref(props.routine.routine.value.anchor ?? '')
// I valori salvati arrivano dal database dopo il primo disegno
watch(() => props.routine.time.value, value => (time.value = value))
watch(() => props.routine.routine.value.anchor, value => (anchor.value = value ?? ''))

function save(changes: Parameters<typeof props.routine.save>[0]) {
  props.routine.save(changes).catch((cause) => {
    console.error('Routine non salvata', cause)
  })
}

function saveTime() {
  if (/^\d{2}:\d{2}$/.test(time.value)) save({ time: time.value })
}

function chooseAnchor(value: string) {
  anchor.value = value
  save({ anchor: value })
}
</script>

<template>
  <section
    class="space-y-4"
    data-testid="routine-form"
  >
    <h2 class="font-semibold">
      La tua routine
    </h2>

    <div class="space-y-2">
      <p class="text-sm font-medium">
        Obiettivo di ogni giorno
      </p>
      <UTabs
        :model-value="String(routine.goalMinutes.value)"
        :items="GOAL_OPTIONS.map(minutes => ({ label: `${minutes} min`, value: String(minutes) }))"
        :content="false"
        size="sm"
        class="w-full"
        @update:model-value="save({ goalMinutes: Number($event) })"
      />
      <p class="text-sm text-muted">
        Contano i minuti con una sessione o il ripasso aperti, anche in ascolto. Meglio poco ogni giorno che tanto ogni tanto.
      </p>
    </div>

    <div class="space-y-2">
      <label
        for="routine-time"
        class="block text-sm font-medium"
      >
        A che ora
      </label>
      <UInput
        id="routine-time"
        v-model="time"
        type="time"
        class="w-32"
        @change="saveTime"
      />
    </div>

    <div class="space-y-2">
      <label
        for="routine-anchor"
        class="block text-sm font-medium"
      >
        Dopo cosa, o dove
      </label>
      <UInput
        id="routine-anchor"
        v-model="anchor"
        placeholder="Per esempio: dopo il caffè"
        class="w-full"
        @change="save({ anchor: anchor.trim() })"
      />
      <div class="flex flex-wrap gap-2">
        <UButton
          v-for="suggestion in ANCHORS"
          :key="suggestion"
          size="xs"
          color="neutral"
          :variant="anchor === suggestion ? 'solid' : 'subtle'"
          :label="suggestion"
          @click="chooseAnchor(suggestion)"
        />
      </div>
      <p class="text-sm text-muted">
        Un'abitudine si tiene meglio se segue qualcosa che fai già ogni giorno.
      </p>
    </div>
  </section>
</template>
