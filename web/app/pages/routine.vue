<script setup lang="ts">
const routine = useRoutine()

useHead({ title: 'Routine di lettura' })
</script>

<template>
  <div class="mx-auto min-h-dvh max-w-2xl pb-10">
    <CommonAppHeader
      title="Routine di lettura"
      back="/"
    />

    <main class="space-y-8 px-4 pt-2">
      <RoutineStats :routine="routine" />
      <RoutineReadingCalendar :routine="routine" />
      <RoutineForm :routine="routine" />
      <RoutineReminderCard :routine="routine" />
    </main>
  </div>
</template>
