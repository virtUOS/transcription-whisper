import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import de from './de.json'
import en from './en.json'

const supportedLanguages = ['de', 'en']
const browserLang = navigator.language.split('-')[0]
const defaultLang = supportedLanguages.includes(browserLang) ? browserLang : 'de'

i18n.use(initReactI18next).init({
  resources: { de: { translation: de }, en: { translation: en } },
  lng: defaultLang,
  fallbackLng: 'de',
  interpolation: { escapeValue: false },
})

export default i18n
