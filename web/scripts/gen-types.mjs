// Genera i tipi TypeScript da schema/bookpack.schema.json. Lo schema nasce dai modelli Pydantic.
import { writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { compileFromFile } from 'json-schema-to-typescript'

const schema = fileURLToPath(new URL('../../schema/bookpack.schema.json', import.meta.url))
const output = fileURLToPath(new URL('../app/types/bookpack.ts', import.meta.url))

const types = await compileFromFile(schema, {
  bannerComment: '/* Generato da scripts/gen-types.mjs: non modificare. Rigenera con `pnpm gen:types`. */',
  style: { semi: false, singleQuote: true },
  // Con i limiti minItems/maxItems si otterrebbero unioni di tuple: bastano array semplici
  maxItems: -1,
})
await writeFile(output, types)
console.log(`Tipi scritti in ${output}`)
