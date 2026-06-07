/** Scrollable Terms or Privacy document. */
export default function LegalDocumentModal({ open, title, sections, onClose }) {
  if (!open) return null

  return (
    <div
      className="legal-doc-backdrop"
      role="presentation"
      onClick={onClose}
      onKeyDown={e => e.key === 'Escape' && onClose()}
    >
      <div
        className="legal-doc"
        role="dialog"
        aria-modal="true"
        aria-labelledby="legal-doc-title"
        onClick={e => e.stopPropagation()}
      >
        <header className="legal-doc__header">
          <h2 id="legal-doc-title" className="legal-doc__title">{title}</h2>
          <button type="button" className="legal-doc__close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>
        <div className="legal-doc__body">
          {sections.map(({ title: sectionTitle, body }) => (
            <section key={sectionTitle} className="legal-doc__section">
              <h3 className="legal-doc__section-title">{sectionTitle}</h3>
              <p className="legal-doc__section-body">{body}</p>
            </section>
          ))}
        </div>
        <footer className="legal-doc__footer">
          <button type="button" className="legal-doc__btn" onClick={onClose}>
            Close
          </button>
        </footer>
      </div>
    </div>
  )
}
