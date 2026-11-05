export default defineNuxtPlugin(() => {
  const { restore } = useSettings()
  restore().catch((cause) => {
    console.error('Impostazioni non ripristinate', cause)
  })
})
