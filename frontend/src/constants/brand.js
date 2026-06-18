/** Central app branding — feature-descriptive naming */
export const APP_NAME = 'Parashara Jyotish'
export const APP_SHORT = 'Parashara'

/** Traditional Ganesha photo (banner + home hero) */
export const APP_GANESHA_IMG = '/images/ganesha-traditional.png'

/** Ganesha mantra — English, Sanskrit (Devanagari), Tamil */
export const APP_MANTRA_EN = 'Om Shri Maha Ganapatheye Namah'
export const APP_MANTRA_SANSKRIT = 'ॐ श्री महा गणपतये नमः'
export const APP_MANTRA_TAMIL = 'ஓம் ஸ்ரீ மஹா கணபதியே நமஹ'

/** One line under the title on the home hero */
export const APP_TAGLINE = 'Free Vedic chart, Dasha & Gochara — AI with daily limits'

/** Credibility strip under tagline */
export const APP_TRUST_LINE = 'Sidereal · Lahiri · Vimshottari · Parashari'

/** Value props on Home (above birth form) — shortcuts to main tabs after chart exists */
export const APP_VALUE_CARDS = [
  {
    icon: '⭐',
    title: 'Birth chart',
    desc: 'D1, D9, Dasha & Ashtakavarga',
    tab: 'chart',
    hint: 'Your sidereal natal chart and dasha timeline',
  },
  {
    icon: '🪐',
    title: 'Transit scores',
    desc: 'Gochara ratings by house',
    tab: 'gochar',
    hint: 'How today’s planets affect your chart',
  },
  {
    icon: '🔮',
    title: 'Ask Jyotish AI',
    desc: 'Chat & daily forecast',
    tab: 'chat',
    hint: 'AI answers grounded in your chart',
  },
]

/** Compact feature pills (home hero) — tab + optional section scroll */
export const APP_FEATURE_LINKS = [
  { label: 'D1 / D9', tab: 'chart' },
  { label: 'Dasha', tab: 'chart' },
  { label: 'Ashtakavarga', tab: 'chart', section: 'ashtakavarga' },
  { label: 'Tamil Doshas', tab: 'chart', section: 'tamil-doshas' },
  { label: 'Indu Lagna', tab: 'chart', section: 'indu-lagna' },
  { label: 'Career', tab: 'career' },
  { label: 'Health', tab: 'health' },
  { label: 'Dosha Radar', tab: 'dosha-radar' },
  { label: 'Gochara', tab: 'gochar' },
  { label: 'Panchangam', tab: 'panchangam' },
  { label: 'AI Chat', tab: 'chat' },
]

/** Longer copy for SEO / meta only */
export const APP_DESCRIPTION =
  'Free Vedic natal chart (D1/D9), Vimshottari Dasha, Ashtakavarga, Gochara forecast with date picker, daily Panchangam, Tara Balam, and AI guidance.'
