import { liveQuery } from 'dexie'

/** Risultato di una query Dexie che si aggiorna da solo quando i dati cambiano. */
export function useLiveQuery<T>(query: () => T | Promise<T>) {
  const data = shallowRef<T>()
  const loaded = ref(false)
  const error = shallowRef<unknown>()

  const subscription = liveQuery(query).subscribe({
    next(value) {
      data.value = value
      loaded.value = true
    },
    error(cause) {
      error.value = cause
      loaded.value = true
    },
  })
  onScopeDispose(() => subscription.unsubscribe())

  return { data, loaded, error }
}
