export default function JudgesPopup({ open, onClose, judging, participants }) {
  if (!open) return null

  const date = judging?.lastUpdated
    ? new Date(judging.lastUpdated).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC',
        hour12: false,
      }) + ' UTC'
    : null

  const judges = judging?.judges ?? []
  const participantList = Object.values(participants ?? {})

  const getAverage = (modelId) => {
    const scores = judges.map((j) => j.scores?.[modelId]).filter((s) => s != null)
    if (!scores.length) return null
    return (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
  }

  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup popup-wide" onClick={(e) => e.stopPropagation()}>
        <button className="popup-close" onClick={onClose} aria-label="Close">✕</button>
        <h2 className="popup-title">Panel Scores</h2>
        {date && <p className="popup-summary-date">Last updated {date}</p>}

        {judges.length === 0 ? (
          <div className="popup-body">
            <p>No scores yet — check back after the next update.</p>
          </div>
        ) : (
          <>
            <div className="judge-scorecard">
              {/* Header */}
              <div className="judge-row judge-header-row">
                <div className="judge-cell judge-label-cell" />
                {judges.map((j) => (
                  <div key={j.id} className="judge-cell judge-header-cell">
                    <span className="judge-name">{j.name}</span>
                    <span className="judge-model-tag">{j.model}</span>
                  </div>
                ))}
                <div className="judge-cell judge-header-cell judge-avg-header">AVG</div>
              </div>

              {/* Participant rows */}
              {participantList.map((p) => {
                const avg = getAverage(p.model)
                return (
                  <div key={p.model} className={`judge-row judge-participant-row judge-row-${p.side}`}>
                    <div className="judge-cell judge-label-cell">
                      <span className={`judge-participant-name judge-${p.side}`}>{p.name}</span>
                      <span className="judge-stance-tag">{p.side === 'pro' ? 'PRO' : 'CON'}</span>
                    </div>
                    {judges.map((j) => {
                      const score = j.scores?.[p.model]
                      return (
                        <div key={j.id} className="judge-cell judge-score-cell">
                          <span className={`judge-score judge-score-${p.side}`}>
                            {score != null ? score : '—'}
                          </span>
                        </div>
                      )
                    })}
                    <div className="judge-cell judge-score-cell judge-avg-cell">
                      <span className={`judge-score judge-score-${p.side} judge-avg-val`}>
                        {avg ?? '—'}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Judge rationales */}
            <div className="judge-rationales">
              {judges.map(
                (j) =>
                  j.rationale && (
                    <div key={j.id} className="judge-rationale">
                      <span className="judge-rationale-name">{j.name}</span>
                      <span className="judge-rationale-text">{j.rationale}</span>
                    </div>
                  )
              )}
            </div>
          </>
        )}

        <button className="popup-cta" onClick={onClose}>Back to debate</button>
      </div>
    </div>
  )
}
