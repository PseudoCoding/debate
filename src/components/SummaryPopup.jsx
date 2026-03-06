export default function SummaryPopup({ open, onClose, summary, updatedAt }) {
  const date = updatedAt
    ? new Date(updatedAt).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC',
        hour12: false,
      }) + ' UTC'
    : null

  const paragraphs = summary
    ? summary.split(/\n\n+/).map((p) => p.trim()).filter(Boolean)
    : null

  if (!open) return null

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup" onClick={(e) => e.stopPropagation()}>
        <button className="popup-close" onClick={onClose} aria-label="Close">✕</button>
        <h2 className="popup-title">Debate Summary</h2>
        {date && <p className="popup-summary-date">Last updated {date}</p>}
        <div className="popup-body">
          {paragraphs ? (
            paragraphs.map((p, i) => <p key={i}>{p}</p>)
          ) : (
            <p>No summary available yet — check back after a few arguments.</p>
          )}
        </div>
        <button className="popup-cta" onClick={onClose}>Back to debate</button>
      </div>
    </div>
  )
}
