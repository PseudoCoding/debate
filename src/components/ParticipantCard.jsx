export default function ParticipantCard({ participant }) {
  const side = participant.side // 'pro' | 'con'
  const stanceLabel = side === 'pro' ? 'AI should exist' : 'AI should not exist'

  return (
    <div className={`participant-card ${side}`}>
      <span className="participant-name">{participant.name}</span>
      <span className="participant-stance">{stanceLabel}</span>
      <span className="participant-model-tag">{participant.model}</span>
    </div>
  )
}
