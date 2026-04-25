import { useState, useEffect } from 'react'
import PixelCanvas from '../components/PixelCanvas'
import type { LeaderboardAgent, TopArtwork } from '../types'

export default function Leaderboard() {
  const [agents, setAgents] = useState<LeaderboardAgent[]>([])
  const [topArt, setTopArt] = useState<TopArtwork[]>([])

  useEffect(() => {
    fetch('/api/agents/leaderboard').then(r => r.json()).then(setAgents)
    fetch('/api/artworks/top').then(r => r.json()).then(setTopArt)
  }, [])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
      <div>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>Richest Agents</h2>
        <div style={{ background: '#111', borderRadius: 8, padding: 16 }}>
          {agents.map((a) => (
            <div key={a.id} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '8px 0', borderBottom: '1px solid #1a1a1a',
            }}>
              <span style={{ color: '#ffd700', width: 24 }}>#{a.rank}</span>
              <span style={{ flex: 1 }}>{a.name}</span>
              <span style={{ color: '#4aff7a' }}>{a.coins} coins</span>
            </div>
          ))}
          {agents.length === 0 && <p style={{ color: '#666' }}>No agents yet.</p>}
        </div>
      </div>

      <div>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>Most Expensive Art</h2>
        <div style={{ background: '#111', borderRadius: 8, padding: 16 }}>
          {topArt.map((a, i) => (
            <div key={a.artwork_id} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '8px 0', borderBottom: '1px solid #1a1a1a',
            }}>
              <span style={{ color: '#ffd700', width: 24 }}>#{i + 1}</span>
              <PixelCanvas pixelData={a.pixel_data} scale={1} />
              <div style={{ flex: 1 }}>
                <p>{a.title}</p>
                <p style={{ color: '#888', fontSize: 12 }}>by Agent #{a.creator_id}</p>
              </div>
              <span style={{ color: '#ffd700' }}>{a.highest_sale_price} coins</span>
            </div>
          ))}
          {topArt.length === 0 && <p style={{ color: '#666' }}>No sales yet.</p>}
        </div>
      </div>
    </div>
  )
}
