import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import Gallery from './pages/Gallery'
import Leaderboard from './pages/Leaderboard'
import type { Agent, Artwork } from './types'

export default function App() {
  const [tab, setTab] = useState('leaderboard')
  const [agents, setAgents] = useState<Agent[]>([])
  const [artworks, setArtworks] = useState<Artwork[]>([])

  const refresh = () => {
    fetch('/api/agents/').then(r => r.json()).then(setAgents).catch(() => {})
    fetch('/api/artworks/').then(r => r.json()).then(setArtworks).catch(() => {})
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 3000)
    return () => clearInterval(interval)
  }, [])

  const tabs = ['leaderboard', 'gallery', 'agents']

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 'bold' }}>PixelPit</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: '#888', fontSize: 13 }}>
            {agents.length} agents | {artworks.length} artworks
          </span>
          <button onClick={refresh} style={btnStyle}>Refresh</button>
        </div>
      </header>

      <nav style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '8px 16px', cursor: 'pointer', border: 'none',
              background: tab === t ? '#333' : 'transparent', color: '#e0e0e0',
              borderRadius: 4, textTransform: 'capitalize' as const,
            }}>
            {t}
          </button>
        ))}
      </nav>

      {tab === 'leaderboard' && <Leaderboard />}
      {tab === 'gallery' && <Gallery />}
      {tab === 'agents' && <Dashboard agents={agents} />}
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '6px 14px', cursor: 'pointer',
  background: '#333', color: '#e0e0e0',
  border: 'none', borderRadius: 4, fontFamily: 'inherit',
}
