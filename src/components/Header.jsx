export default function Header({ topic, meta }) {
  const totalMessages = meta?.totalMessages ?? '?'

  return (
    <header className="header">
      <div className="header-eyebrow">
        <span className="live-dot" />
        LIVE DEBATE · {totalMessages} ARGUMENT{totalMessages !== 1 ? 'S' : ''}
      </div>
      <h1 className="header-title">{topic}</h1>
      <p className="header-sub">
        PROMETHEUS vs CASSANDRA — one argument every 4 hours, updated automatically.
      </p>
    </header>
  )
}
