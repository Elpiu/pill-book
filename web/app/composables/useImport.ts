import { db, saveBook } from '~/db'
import type { BookPack } from '~/types/bookpack'
import { parseAndValidatePack, type PackValidation } from '~/utils/validatePack'

export function useImport() {
  const pack = shallowRef<BookPack>()
  const errors = ref<string[]>([])
  const loading = ref(false)
  const alreadyImported = ref(false)

  async function accept(result: PackValidation) {
    if (!result.ok) {
      pack.value = undefined
      errors.value = result.errors
      return
    }
    errors.value = []
    alreadyImported.value = Boolean(await db.books.get(result.pack.book.id))
    pack.value = result.pack
  }

  async function run(load: () => Promise<PackValidation>) {
    loading.value = true
    pack.value = undefined
    errors.value = []
    try {
      await accept(await load())
    }
    catch (cause) {
      errors.value = [cause instanceof Error ? cause.message : String(cause)]
    }
    finally {
      loading.value = false
    }
  }

  function fromFile(file: File) {
    return run(async () => parseAndValidatePack(await file.text()))
  }

  function fromUrl(url: string) {
    return run(async () => {
      let response: Response
      try {
        response = await fetch(url)
      }
      catch {
        throw new Error('Impossibile scaricare il file: controlla l\'indirizzo e la connessione. Il server deve anche consentire le richieste da altri siti (CORS).')
      }
      if (!response.ok) throw new Error(`Il server ha risposto con un errore (${response.status}).`)
      return parseAndValidatePack(await response.text())
    })
  }

  async function save(): Promise<string | undefined> {
    if (!pack.value) return undefined
    await saveBook(pack.value)
    return pack.value.book.id
  }

  function clear() {
    pack.value = undefined
    errors.value = []
  }

  return { pack, errors, loading, alreadyImported, fromFile, fromUrl, save, clear }
}
