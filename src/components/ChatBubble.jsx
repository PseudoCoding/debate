function DateDivider({ timestamp }) {
  const label = new Date(timestamp).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
  return (
    <div className="day-divider">
      <div className="day-divider-line" />
      <span className="day-divider-label">{label}</span>
      <div className="day-divider-line" />
    </div>
  )
}

function formatTime(timestamp) {
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
      hour12: false,
    }) + ' UTC'
  } catch {
    return ''
  }
}

export default function ChatBubble({ message, participant }) {
  const side = participant?.side ?? 'pro'
  const name = participant?.name ?? message.model
  const paragraphs = message.content
    .split(/\n\n+/)
    .map((p) => p.trim())
    .filter(Boolean)

  return (
    <>
      {message.isFirstOfDay && <DateDivider timestamp={message.timestamp} />}

      <div className={`bubble-wrapper ${side}`}>
        <div className="bubble-meta">
          <span className="bubble-model-name">{name}</span>
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
