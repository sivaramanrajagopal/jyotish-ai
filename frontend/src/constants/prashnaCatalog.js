/**
 * Full Prashna category + question catalog (bundled — works even if API is stale).
 * Keep in sync with backend/agents/prashna/constants.py
 */

export const PRASHNA_CATALOG = [
  {
    key: 'career',
    label: 'Career / Promotion',
    icon: '🏆',
    house: 10,
    questions: [
      { id: 'promotion', text: 'Will I get a promotion soon?' },
      { id: 'job_offer', text: 'Will I receive a job offer?' },
      { id: 'job_change', text: 'Is changing jobs favourable now?' },
      { id: 'business', text: 'Will my business venture succeed?' },
      { id: 'interview_career', text: 'Will my job interview be successful?' },
      { id: 'recognition', text: 'Will I receive professional recognition?' },
    ],
  },
  {
    key: 'marriage',
    label: 'Marriage / Relationship',
    icon: '💑',
    house: 7,
    questions: [
      { id: 'marriage_soon', text: 'Will marriage happen soon?' },
      { id: 'relationship', text: 'Is this relationship favourable?' },
      { id: 'reconcile', text: 'Will reconciliation with my partner occur?' },
      { id: 'proposal', text: 'Will a proposal be accepted?' },
      { id: 'partner_commitment', text: 'Will my partner commit to this relationship?' },
    ],
  },
  {
    key: 'money',
    label: 'Money / Finance',
    icon: '💰',
    house: 2,
    questions: [
      { id: 'financial_gain', text: 'Will I gain financially soon?' },
      { id: 'loan', text: 'Will I get the loan or funding I need?' },
      { id: 'investment', text: 'Is this investment favourable?' },
      { id: 'debt', text: 'Will I overcome financial difficulty?' },
      { id: 'salary_raise', text: 'Will my income increase?' },
    ],
  },
  {
    key: 'property',
    label: 'Property / Real Estate',
    icon: '🏠',
    house: 4,
    questions: [
      { id: 'buy_property', text: 'Will I buy property successfully?' },
      { id: 'sell_property', text: 'Will I sell my property favourably?' },
      { id: 'vehicle', text: 'Will I acquire a vehicle soon?' },
      { id: 'home_peace', text: 'Will peace and happiness at home improve?' },
    ],
  },
  {
    key: 'health',
    label: 'Health',
    icon: '⚕️',
    house: 6,
    questions: [
      { id: 'recovery', text: 'Will recovery from illness occur?' },
      { id: 'treatment', text: 'Will the treatment be effective?' },
      { id: 'surgery', text: 'Is surgery advisable and favourable?' },
      { id: 'chronic_ease', text: 'Will my health condition improve?' },
    ],
  },
  {
    key: 'travel',
    label: 'Travel',
    icon: '✈️',
    house: 9,
    questions: [
      { id: 'travel_abroad', text: 'Will foreign travel materialise?' },
      { id: 'trip_safe', text: 'Will my journey be safe and successful?' },
      { id: 'visa', text: 'Will visa or travel approval come through?' },
      { id: 'pilgrimage', text: 'Is pilgrimage or long journey favourable?' },
    ],
  },
  {
    key: 'education',
    label: 'Education',
    icon: '📚',
    house: 5,
    questions: [
      { id: 'admission', text: 'Will I get admission to the desired course?' },
      { id: 'exam_pass', text: 'Will I pass the upcoming exam?' },
      { id: 'scholarship', text: 'Will I receive a scholarship or grant?' },
      { id: 'study_success', text: 'Will my studies succeed this term?' },
    ],
  },
  {
    key: 'lost_and_found',
    label: 'Lost & Found',
    icon: '🔍',
    house: 4,
    questions: [
      { id: 'recover_lost', text: 'Will I recover my lost item?' },
      { id: 'still_findable', text: 'Is the lost article still findable?' },
      { id: 'where_direction', text: 'Is recovery of the lost object indicated?' },
      { id: 'stolen', text: 'If stolen, is return of the item possible?' },
      { id: 'lost_document', text: 'Will I find my lost document or ID?' },
    ],
  },
  {
    key: 'competitive_exam',
    label: 'Competitive Exam',
    icon: '📝',
    house: 6,
    questions: [
      { id: 'pass_exam', text: 'Will I pass the competitive exam?' },
      { id: 'get_selected', text: 'Will I get selected in the exam?' },
      { id: 'rank', text: 'Will I achieve a good rank or score?' },
      { id: 'interview', text: 'Will the interview stage be successful?' },
      { id: 'govt_exam', text: 'Will I clear the government competitive exam?' },
    ],
  },
  {
    key: 'key_interest',
    label: 'Key Areas of Interest',
    icon: '⭐',
    house: 11,
    questions: [
      { id: 'h1_self', text: 'H1 Self — Is my health and vitality favourable now?' },
      { id: 'h2_wealth', text: 'H2 Wealth — Is financial gain indicated now?' },
      { id: 'h3_courage', text: 'H3 Courage — Are communication and efforts supported?' },
      { id: 'h4_home', text: 'H4 Home — Is home and property matter favourable?' },
      { id: 'h5_education', text: 'H5 Education — Are creativity and studies favoured?' },
      { id: 'h6_health', text: 'H6 Health — Can I overcome illness or competition?' },
      { id: 'h7_marriage', text: 'H7 Marriage — Is partnership favourable now?' },
      { id: 'h8_obstacles', text: 'H8 Obstacles — Will sudden blockages resolve?' },
      { id: 'h9_fortune', text: 'H9 Fortune — Is luck and dharma on my side?' },
      { id: 'h10_career', text: 'H10 Career — Is professional success indicated?' },
      { id: 'h11_gains', text: 'H11 Gains — Will wishes and income manifest?' },
      { id: 'h12_spiritual', text: 'H12 Spiritual — Is foreign or spiritual path favourable?' },
      { id: 'most_favourable', text: 'Which life area looks most favourable overall?' },
    ],
  },
  {
    key: 'general',
    label: 'General',
    icon: '🔮',
    house: 11,
    questions: [
      { id: 'overall', text: 'Is the overall outlook favourable now?' },
      { id: 'wish', text: 'Will my current wish be fulfilled?' },
      { id: 'obstacle', text: 'Will the main obstacle be removed?' },
      { id: 'decision', text: 'Is my current decision favourable?' },
    ],
  },
]

/** Merge API categories with local questions when API omits them (old backend). */
export function mergePrashnaCatalog(apiCategories) {
  const localByKey = Object.fromEntries(PRASHNA_CATALOG.map(c => [c.key, c]))
  if (!apiCategories?.length) return PRASHNA_CATALOG

  return apiCategories.map(apiCat => {
    const local = localByKey[apiCat.key]
    const questions = apiCat.questions?.length ? apiCat.questions : (local?.questions || [])
    return {
      ...local,
      ...apiCat,
      questions,
      icon: apiCat.icon || local?.icon || '🔮',
    }
  })
}

export function firstQuestionId(catalog, categoryKey) {
  const cat = catalog.find(c => c.key === categoryKey) || catalog[0]
  return cat?.questions?.[0]?.id || ''
}
