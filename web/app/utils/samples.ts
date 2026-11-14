/**
 * Libri d'esempio pubblicati con l'app, in `public/samples/`: lo stesso libro di pubblico dominio in
 * più lingue, utile anche per provare le voci dell'ascolto.
 */
export const SAMPLES = [
  { file: 'how-to-live-on-24-hours-a-day.bookpack.json', label: 'Esempio in italiano' },
  { file: 'how-to-live-on-24-hours-a-day.en.bookpack.json', label: 'Esempio in inglese' },
]

export function sampleUrl(baseURL: string, file: string): string {
  return `${baseURL}samples/${file}`
}
