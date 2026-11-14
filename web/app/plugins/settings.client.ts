export default defineNuxtPlugin(() => {
  const { restore } = useSettings()
  const listen = useListenSettings()
  Promise.all([restore(), listen.restore()]).catch((cause) => {
    console.error('Impostazioni non ripristinate', cause)
  })
})
