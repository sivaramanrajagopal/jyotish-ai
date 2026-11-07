export function ordinal(n) {
  const v = Number(n)
  if (!v) return '—'
  const s = v % 100 >= 11 && v % 100 <= 13 ? 'th' : { 1: 'st', 2: 'nd', 3: 'rd' }[v % 10] || 'th'
  return `${v}${s}`
}

export function houseTitle(row, language = 'english') {
  const theme = language === 'tamil' ? row.theme_ta || row.theme_en : row.theme_en
  return `${row.ordinal} · ${theme}`
}
