import { getSetting, setSetting } from '~/db'

export const FONT_SCALES = [
  { value: 0.9, label: 'Piccolo' },
  { value: 1, label: 'Normale' },
  { value: 1.15, label: 'Grande' },
  { value: 1.3, label: 'Molto grande' },
]

export type ThemePreference = 'system' | 'light' | 'dark'

function applyFontScale(scale: number) {
  document.documentElement.style.setProperty('--card-scale', String(scale))
}

export function useSettings() {
  const fontScale = useState('font-scale', () => 1)
  const colorMode = useColorMode()

  async function restore() {
    const [savedScale, savedTheme] = await Promise.all([
      getSetting<number>('fontScale'),
      getSetting<ThemePreference>('theme'),
    ])
    if (typeof savedScale === 'number') {
      fontScale.value = savedScale
      applyFontScale(savedScale)
    }
    if (savedTheme) colorMode.preference = savedTheme
  }

  async function setFontScale(scale: number) {
    fontScale.value = scale
    applyFontScale(scale)
    await setSetting('fontScale', scale)
  }

  async function setTheme(theme: ThemePreference) {
    colorMode.preference = theme
    await setSetting('theme', theme)
  }

  return { fontScale, theme: computed(() => colorMode.preference as ThemePreference), restore, setFontScale, setTheme }
}
