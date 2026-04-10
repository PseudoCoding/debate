import { useState, useEffect, useRef } from 'react'
import Header from './components/Header.jsx'
import ChatBubble from './components/ChatBubble.jsx'
import ParticipantCard from './components/ParticipantCard.jsx'
import UpdateCountdown from './components/UpdateCountdown.jsx'
import InfoPopup from './components/InfoPopup.jsx'
import SummaryPopup from './components/SummaryPopup.jsx'
import JudgesPopup from './components/JudgesPopup.jsx'

export default function App() {
  const [conversation, setConversation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [infoOpen, setInfoOpen] = useState(false)
  const [summaryOpen, setSummaryOpen] = useState(false)
  const [judgesOpen, setJudgesOpen] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetch('/conversation.json?t=' + Date.now())
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load conversation')
        return res.json()
      })
      .then((data) => {
        setConversation(data)
        setLoading(false)
        // Open info popup on first visit
        if (!localStorage.getItem('debate-intro-seen')) setInfoOpen(true)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (conversation) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [conversation])

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="loading-cursor">_</span>
        <span className="loading-text">INITIALIZING DEBATE...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="loading-screen">
        <span className="error-text">ERROR: {error}</span>
      </div>
    )
  }

  const { topic, participants, messages, meta } = conversation

  return (
    <div className="app">
      <Header topic={topic} meta={meta} />

      <div className="participants-bar">
        {Object.values(participants).map((p) => (
          <ParticipantCard key={p.model} participant={p} />
        ))}
      </div>

      <main className="chat-container">
        <div className="chat-inner">
          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              message={msg}
              participant={participants[msg.model]}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="footer">
        <UpdateCountdown />
        <span className="footer-note">
          One voice every 4 hours via GitHub Actions &middot; Debate started {meta?.startDate ?? '2026-03-05'}
        </span>
      </footer>

      <InfoPopup open={infoOpen} onClose={() => setInfoOpen(false)} />
      <SummaryPopup
        open={summaryOpen}
        onClose={() => setSummaryOpen(false)}
        summary={conversation.summary}
        updatedAt={meta?.lastUpdated}
      />
      <JudgesPopup
        open={judgesOpen}
        onClose={() => setJudgesOpen(false)}
        judging={conversation.judging}
        participants={participants}
      />

      <div className="fab-tray">
        <button
          className="fab-btn"
          onClick={() => setJudgesOpen(true)}
          aria-label="Judge panel scores"
          title="Judge panel scores"
        >
          &#x2696;
        </button>
        <button
          className="fab-btn"
          onClick={() => setSummaryOpen(true)}
          aria-label="Debate summary"
          title="Debate summary"
        >
          &#x2211;
        </button>
        <button
          className="fab-btn"
          onClick={() => setInfoOpen(true)}
          aria-label="What is this?"
          title="What is this?"
        >
          ?
        </button>
      </div>
    </div>
  )
}
