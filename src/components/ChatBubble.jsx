function DayDivider({ day }) {
  return (
    <div className="day-divider">
      <div className="day-divider-line" />
      <span className="day-divider-label">Day {day}</span>
      <div className="day-divider-line" />
    </div>
  )
}

function formatTime(timestamp) {
  try {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return ''
  }
}

export default function ChatBubble({ message, participant, isFirst }) {
  const side = participant?.side ?? 'pro'
  const name = participant?.name ?? message.model
  const paragraphs = message.content
    .split(/\n\n+/)
    .map((p) => p.trim())
    .filter(Boolean)

  return (
    <>
      {/* Show a day divider before the first message of each day */}
      {message.isFirstOfDay && <DayDivider day={message.day} />}

      <div className={`bubble-wrapper ${side}`}>
        <div className="bubble-meta">
          <span className="bubble-model-name">{name}</span>
          <span className="bubble-day">· Day {message.day}</span>
          <span className="bubble-time">{formatTime(message.timestamp)}</span>
        </div>
        <div className="bubble-body">
          {paragraphs.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
      </div>
    </>
  )
}
