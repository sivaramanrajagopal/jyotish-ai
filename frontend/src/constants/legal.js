import { APP_NAME } from './brand'

export const LEGAL_VERSION = '2026-06-07'
export const LEGAL_STORAGE_KEY = `jyotish-legal-${LEGAL_VERSION}`

export const CONTACT_EMAIL =
  import.meta.env.VITE_CONTACT_EMAIL || 'adtrackmail@gmail.com'

export const SHORT_DISCLAIMER =
  `${APP_NAME} provides Vedic astrology content — including natal charts, dasha periods, ` +
  'transit forecasts, panchangam, ashtakavarga, and AI-generated text — for informational ' +
  'and entertainment purposes only. It is not medical, health, mental-health, legal, financial, ' +
  'investment, or professional advice. Do not rely on this app as a substitute for qualified ' +
  'professionals. Astrological interpretations are subjective and not scientifically verified; ' +
  'no accuracy or outcome is guaranteed. Use at your own risk. If you have a medical emergency ' +
  'or mental-health crisis, contact emergency services or a qualified provider immediately.'

export const TERMS_SECTIONS = [
  {
    title: '1. Acceptance',
    body:
      `By accessing or using ${APP_NAME} ("the Service"), you agree to these Terms of Use. ` +
      'If you do not agree, you must not use the Service.',
  },
  {
    title: '2. Eligibility',
    body:
      'You must be at least 18 years of age to use the Service. By using the Service, you ' +
      'represent and warrant that you are 18 or older and have the legal capacity to enter ' +
      'into these Terms under applicable law in India.',
  },
  {
    title: '3. Nature of the Service',
    body:
      'The Service is provided for general information and entertainment only. Content is ' +
      'generated from astrological calculations and, where applicable, artificial intelligence. ' +
      'It does not create a client–advisor, doctor–patient, attorney–client, or fiduciary relationship.',
  },
  {
    title: '4. No professional advice',
    body:
      'Nothing in the Service constitutes medical, psychological, legal, tax, investment, or ' +
      'other professional advice. Always seek advice from licensed or qualified professionals ' +
      'for decisions affecting your health, finances, legal rights, or safety.',
  },
  {
    title: '5. No warranties',
    body:
      'The Service is provided "as is" and "as available" without warranties of any kind, ' +
      'express or implied, including merchantability, fitness for a particular purpose, or ' +
      'non-infringement. We do not warrant that calculations, forecasts, or AI responses are ' +
      'accurate, complete, or current.',
  },
  {
    title: '6. Limitation of liability',
    body:
      'To the fullest extent permitted by applicable law in India, the operators, owners, ' +
      'developers, and affiliates of the Service shall not be liable for any indirect, incidental, ' +
      'special, consequential, or punitive damages, or any loss of profits, data, or goodwill, ' +
      'arising from your use of or reliance on the Service, even if advised of the possibility ' +
      'of such damages. Your sole remedy is to stop using the Service.',
  },
  {
    title: '7. User responsibility',
    body:
      'You are solely responsible for decisions and actions you take based on the Service. ' +
      'You agree not to misuse the Service, attempt to bypass rate limits, or use automated ' +
      'tools to extract data or consume AI resources excessively.',
  },
  {
    title: '8. AI-generated content',
    body:
      'AI-generated responses may be incorrect, incomplete, or inappropriate. Do not treat them ' +
      'as factual, authoritative, or suitable for critical life decisions.',
  },
  {
    title: '9. Accounts and data',
    body:
      'You may create an account to save your chart. You may delete your account and associated ' +
      'data at any time from the Home tab. We may suspend or terminate access for abuse or ' +
      'violation of these Terms.',
  },
  {
    title: '10. Governing law',
    body:
      'These Terms are governed by the laws of India, without regard to conflict-of-law principles. ' +
      'Courts in India shall have exclusive jurisdiction, subject to applicable consumer protection laws.',
  },
  {
    title: '11. Contact',
    body: `Questions about these Terms: ${CONTACT_EMAIL}`,
  },
]

export const PRIVACY_SECTIONS = [
  {
    title: '1. Overview',
    body:
      `This Privacy Policy describes how ${APP_NAME} collects, uses, and stores information when you use the Service.`,
  },
  {
    title: '2. Information we collect',
    body:
      'Birth details you enter (name, date of birth, time, place of birth, gender); account email ' +
      'if you sign in; technical data such as browser type; hashed IP address for guest AI rate limits; ' +
      'AI usage counts; and optional product analytics events (e.g. chart calculated, chat sent).',
  },
  {
    title: '3. How we use information',
    body:
      'To calculate and display your natal chart; save your chart when signed in; provide Panchangam, ' +
      'forecast, and AI chat features; enforce fair-use limits; improve reliability and security; ' +
      'and respond to support requests.',
  },
  {
    title: '4. Storage and processors',
    body:
      'Data is stored using Supabase (PostgreSQL). Guest chart data may be held in browser session ' +
      'storage for up to 24 hours. We use hosting providers (e.g. Vercel, Render), Supabase, and ' +
      'OpenAI for AI features. These processors handle data under their respective terms.',
  },
  {
    title: '5. Retention',
    body:
      'Signed-in data is retained until you delete your account. Guest session data expires when ' +
      'you clear browser session storage or after approximately 24 hours. Aggregated analytics may be retained longer.',
  },
  {
    title: '6. Your choices',
    body:
      'You can delete your account and chart from the Home tab (Account section). You may clear guest ' +
      'session data using Clear chart. Contact us to request assistance with data questions.',
  },
  {
    title: '7. Children',
    body:
      'The Service is not intended for users under 18. We do not knowingly collect data from anyone under 18.',
  },
  {
    title: '8. Security',
    body:
      'We use industry-standard practices including HTTPS, access controls, and rate limiting. No method ' +
      'of transmission or storage is 100% secure.',
  },
  {
    title: '9. Changes',
    body:
      'We may update this Policy. Material changes will be reflected by updating the version date. ' +
      'Continued use after changes constitutes acceptance.',
  },
  {
    title: '10. Contact',
    body: `Privacy questions or data requests: ${CONTACT_EMAIL}`,
  },
]
