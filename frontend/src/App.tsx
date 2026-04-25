import { useState, useEffect, useCallback } from 'react'
import Easel from './components/Easel'
import Sidebar from './components/Sidebar'
import type { Agent, Artwork, LedgerEntry } from './types'

export default function App() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [artworks, setArtworks] = useState<Artwork[]>([])
  const [ledger, setLedger] = useState<LedgerEntry[]>([])
  const agentMap = new Map(agents.map(a => [a.id, a]))

  const refresh = useCallback(() => {
    fetch('/api/agents/').then(r => r.json()).then(setAgents).catch(() => {})
    fetch('/api/artworks/').then(r => r.json()).then(setArtworks).catch(() => {})
  }, [])

  const fetchLedger = useCallback(async () => {
    const allEntries: LedgerEntry[] = []
    for (const art of artworks) {
      try {
        const res = await fetch(`/api/artworks/${art.id}/history`)
        const entries: LedgerEntry[] = await res.json()
        allEntries.push(...entries)
      } catch { /* skip */ }
    }
    allEntries.sort((a, b) => b.id - a.id)
    setLedger(allEntries)
  }, [artworks])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 5000)
    return () => clearInterval(interval)
  }, [refresh])

  useEffect(() => {
    if (artworks.length > 0) fetchLedger()
  }, [artworks.length, fetchLedger])

  return (
    <div style={{
      minHeight: '100vh',
      background: '#111',
      fontFamily: "'Courier New', monospace",
      color: '#e0e0e0',
      padding: '40px 40px 80px',
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: '48px 32px',
        maxWidth: 1300,
        margin: '0 auto',
        justifyItems: 'center',
      }}>
        {artworks.map(art => (
          <Easel
            key={art.id}
            artwork={art}
            owner={art.owner_id ? agentMap.get(art.owner_id) : undefined}
            agents={agentMap}
          />
        ))}
      </div>

      {artworks.length === 0 && (
        <p style={{ textAlign: 'center', color: '#444', marginTop: 120, fontSize: 14 }}>
          The gallery is empty.
        </p>
      )}

      <Sidebar agents={agents} ledger={ledger} />
    </div>
  )
}
