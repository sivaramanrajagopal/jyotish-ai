import { SHORT_DISCLAIMER, CONTACT_EMAIL } from '../constants/legal'
import { APP_NAME } from '../constants/brand'

export default function LegalFooter({ onOpenTerms, onOpenPrivacy, onOpenDisclaimer }) {
  return (
    <footer className="legal-footer" role="contentinfo">
      <p className="legal-footer__disclaimer">{SHORT_DISCLAIMER}</p>
      <nav className="legal-footer__nav" aria-label="Legal">
        <button type="button" className="legal-footer__link" onClick={onOpenDisclaimer}>
          Disclaimer
        </button>
        <span className="legal-footer__sep" aria-hidden="true">·</span>
        <button type="button" className="legal-footer__link" onClick={onOpenTerms}>
          Terms of Use
        </button>
        <span className="legal-footer__sep" aria-hidden="true">·</span>
        <button type="button" className="legal-footer__link" onClick={onOpenPrivacy}>
          Privacy Policy
        </button>
        <span className="legal-footer__sep" aria-hidden="true">·</span>
        <a className="legal-footer__link legal-footer__link--anchor" href={`mailto:${CONTACT_EMAIL}`}>
          Contact
        </a>
      </nav>
      <p className="legal-footer__copy">
        © {new Date().getFullYear()} {APP_NAME}. For entertainment and informational purposes only.
      </p>
    </footer>
  )
}
