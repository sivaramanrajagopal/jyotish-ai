import { useEffect, useState } from 'react'
import { APP_NAME } from '../constants/brand'
import { SHORT_DISCLAIMER } from '../constants/legal'
import { saveLegalConsent } from '../lib/legalConsent'

export default function LegalAcceptModal({ open, onAccepted, onOpenTerms, onOpenPrivacy }) {
  const [ageOk, setAgeOk] = useState(false)
  const [termsOk, setTermsOk] = useState(false)

  useEffect(() => {
    if (!open) {
      setAgeOk(false)
      setTermsOk(false)
    }
  }, [open])

  if (!open) return null

  const canAccept = ageOk && termsOk

  const handleAccept = () => {
    if (!canAccept) return
    saveLegalConsent()
    onAccepted()
  }

  return (
    <div className="legal-accept-backdrop" role="presentation">
      <div
        className="legal-accept"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="legal-accept-title"
        aria-describedby="legal-accept-desc"
      >
        <h2 id="legal-accept-title" className="legal-accept__title">
          Welcome to {APP_NAME}
        </h2>
        <p id="legal-accept-desc" className="legal-accept__disclaimer">
          {SHORT_DISCLAIMER}
        </p>

        <label className="legal-accept__check">
          <input
            type="checkbox"
            checked={ageOk}
            onChange={e => setAgeOk(e.target.checked)}
          />
          <span>I confirm I am <strong>18 years of age or older</strong> and located in a jurisdiction where I may use this Service.</span>
        </label>

        <label className="legal-accept__check">
          <input
            type="checkbox"
            checked={termsOk}
            onChange={e => setTermsOk(e.target.checked)}
          />
          <span>
            I have read and agree to the{' '}
            <button type="button" className="legal-accept__link" onClick={onOpenTerms}>Terms of Use</button>
            {' '}and{' '}
            <button type="button" className="legal-accept__link" onClick={onOpenPrivacy}>Privacy Policy</button>.
          </span>
        </label>

        <button
          type="button"
          className="legal-accept__btn"
          disabled={!canAccept}
          onClick={handleAccept}
        >
          I understand — continue
        </button>
      </div>
    </div>
  )
}
