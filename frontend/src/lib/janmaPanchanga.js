/** Birth tithi, yoga, and karana from natal longitudes. Mirrors backend/agents/janma_panchanga.py. */

const TITHIS = [
  'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
  'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
  'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
  'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya',
]

const YOGAS = [
  'Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana',
  'Atiganda', 'Sukarma', 'Dhriti', 'Shula', 'Ganda',
  'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra',
  'Siddhi', 'Vyatipata', 'Variyana', 'Parigha', 'Shiva',
  'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma',
  'Indra', 'Vaidhriti',
]

const MOVABLE = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Garija', 'Vanija', 'Vishti']
const FIXED = ['Kimstughna', 'Shakuni', 'Chatushpada', 'Naga']
const VAARA = [
  ['Somavaram', 'Moon'],
  ['Mangalavaram', 'Mars'],
  ['Budhavaram', 'Mercury'],
  ['Guruvaram', 'Jupiter'],
  ['Shukravaram', 'Venus'],
  ['Shanivaram', 'Saturn'],
  ['Bhanuavaram', 'Sun'],
]

const PRACTICE = {
  Bava: ['பவம்', 'movable', 'Mars', 'செவ்வாய்', 'Indra', 'இந்திரன்', 'Lion', 'சிங்கம்'],
  Balava: ['பாலவம்', 'movable', 'Rahu', 'ராகு', 'Prajapati', 'பிரஜாபதி', 'Tiger', 'புலி'],
  Kaulava: ['கௌலவம்', 'movable', 'Saturn', 'சனி', 'Mitra', 'மித்திரன்', 'Boar', 'பன்றி'],
  Taitila: ['தைதுலை', 'movable', 'Venus', 'சுக்கிரன்', 'Pitris', 'பித்ருக்கள்', 'Donkey', 'கழுதை'],
  Garija: ['கரசை', 'movable', 'Moon', 'சந்திரன்', 'Bhumadevi', 'பூமாதேவி', 'Elephant', 'யானை', 'Karajai'],
  Vanija: ['வணிசை', 'movable', 'Sun', 'சூரியன்', 'Sri', 'ஸ்ரீ தேவி', 'Bull', 'காளை'],
  Vishti: ['பத்திரை', 'movable', 'Ketu', 'கேது', 'Yama', 'யமன்', 'Rooster', 'சேவல்', 'Bhadra'],
  Shakuni: ['சகுனி', 'fixed', 'Saturn', 'சனி', 'Vishnu', 'விஷ்ணு', 'Crow', 'காகம்'],
  Chatushpada: ['சதுஷ்பாதம்', 'fixed', 'Jupiter', 'குரு', 'Manibhadra', 'மணிபத்ரன்', 'Dog', 'நாய்'],
  Naga: ['நாகவம்', 'fixed', 'Rahu', 'ராகு', 'Naga', 'சர்ப்பம்', 'Snake', 'பாம்பு'],
  Kimstughna: ['கிம்ஸ்துக்னம்', 'fixed', 'Mercury', 'புதன்', 'Vayu', 'வாயு', 'Worm', 'புழு'],
}

function karanaName(raw) {
  if (raw === 0) return FIXED[0]
  if (raw >= 57) {
    const fixedIdx = raw - 57
    return fixedIdx < 3 ? FIXED[fixedIdx + 1] : FIXED[3]
  }
  return MOVABLE[(raw - 1) % 7]
}

function record(name) {
  const row = PRACTICE[name]
  if (!row) return { name, name_ta: '', alias: '', kind: '', lord: '', lord_ta: '', deity: '', deity_ta: '', animal: '', animal_ta: '', practice: { en: '', ta: '' } }
  const [name_ta, kind, lord, lord_ta, deity, deity_ta, animal, animal_ta, alias] = row
  return {
    name,
    name_ta,
    alias: alias || '',
    kind,
    lord,
    lord_ta,
    deity,
    deity_ta,
    animal,
    animal_ta,
    practice: {
      en: `Keep a picture of the ${animal.toLowerCase()} where you see it often, as a phone or desktop wallpaper. A simple practice for this karana, not a promise of results.`,
      ta: `${animal_ta} படத்தை திரை அல்லது கணினி பின்னணியில் வையுங்கள். இது ஒரு எளிய பழக்கம்.`,
    },
  }
}

export function allKaranas() {
  return Object.keys(PRACTICE).map(record)
}

export function buildJanmaPanchanga(chart) {
  if (chart?.janma_panchanga?.tithi) return chart.janma_panchanga
  const sun = Number(chart?.planet_positions?.Sun?.longitude) || 0
  const moonRow = chart?.planet_positions?.Moon || {}
  const moon = Number(moonRow.longitude) || 0
  const diff = ((moon - sun) % 360 + 360) % 360
  const tithiIdx = Math.floor(diff / 12) % 30
  const yogaIdx = Math.floor((((moon + sun) % 360 + 360) % 360) / (360 / 27)) % 27
  const dob = chart?.birth_data?.dob || ''
  const weekday = dob ? new Date(`${dob.slice(0, 10)}T12:00:00`).getDay() : 1
  const vaaraIdx = weekday === 0 ? 6 : weekday - 1
  const approximate = Boolean(chart?.birth_data?.birth_time_approximate)
  return {
    vaara: { name: VAARA[vaaraIdx][0], lord: VAARA[vaaraIdx][1] },
    tithi: {
      name: TITHIS[tithiIdx],
      paksha: tithiIdx < 15 ? 'Shukla' : 'Krishna',
      index: (tithiIdx % 15) + 1,
    },
    nakshatra: {
      name: moonRow.nakshatra || '',
      pada: moonRow.pada,
      lord: moonRow.nakshatra_lord || '',
    },
    yoga: { name: YOGAS[yogaIdx] },
    karana: record(karanaName(Math.floor(diff / 6) % 60)),
    karanas: allKaranas(),
    time_is_noon: approximate,
    note: approximate
      ? 'Tithi, yoga, and karana are taken at 12:00 noon because the birth time was marked unknown. They can fall in the next half of the tithi.'
      : 'Tithi, yoga, and karana are taken at the birth time.',
  }
}
