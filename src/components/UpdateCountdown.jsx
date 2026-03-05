import { useState, useEffect } from 'react'

// Updates fire at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
function getTimeUntilNext4Hour() {
  const now = new Date()
  const currentUTCHour = now.getUTCHours()
  const nextBoundaryHour = (Math.floor(currentUTCHour / 4) + 1) * 4
  const next = new Date(now)
  if (nextBoundaryHour >= 24) {
    next.setUTCDate(next.getUTCDate() + 1)
    next.setUTCHours(0, 0, 0, 0)
  } else {
    next.setUTCHours(nextBoundaryHour, 0, 0, 0)
  }
  const diff = next - now
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  const nextSlotLabel = String(nextBoundaryHour >= 24 ? 0 : nextBoundaryHour).padStart(2, '0') + ':00 UTC'
  return { h, m, s, nextSlotLabel }
}

export default function UpdateCountdown() {
  const [time, setTime] = useState(getTimeUntilNext4Hour())

  useEffect(() => {
    const id = setInterval(() => setTime(getTimeUntilNext4Hour()), 1000)
    return () => clearInterval(id)
  }, [])

  const pad = (n) => String(n).padStart(2, '0')

  return (
    <div className="countdown">
      Next argument at {time.nextSlotLabel} — in{' '}
      <strong>
        {pad(time.h)}:{pad(time.m)}:{pad(time.s)}
      </strong>
    </div>
  )
}
