import { useState, useEffect, useCallback, useRef } from 'react'
import Easel from './components/Easel'
import AgentAvatar from './components/AgentAvatar'
import Sidebar from './components/Sidebar'
import type { Agent, Artwork, LedgerEntry } from './types'
import { BACKGROUNDS, type Background } from './backgrounds'

export default function App() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [artworks, setArtworks] = useState<Artwork[]>([])
  const [ledger, setLedger] = useState<LedgerEntry[]>([])
  const [bg, setBg] = useState<Background>(BACKGROUNDS[0])
  const [showBgPicker, setShowBgPicker] = useState(false)
  const agentMap = new Map(agents.map(a => [a.id, a]))
  const easelRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const gridRef = useRef<HTMLDivElement>(null)

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
    <div ref={gridRef} style={{
      minHeight: '100vh',
      background: bg.css,
      fontFamily: "'Courier New', monospace",
      color: '#e0e0e0',
      padding: '40px 40px 80px',
      position: 'relative',
    }}>
      {/* Floor strip */}
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, height: '22%',
        background: bg.floor,
        borderTop: `2px solid ${bg.floorBorder}`,
        pointerEvents: 'none', zIndex: 0,
      }} />

      {/* Background picker — bottom left */}
      <div style={{ position: 'fixed', bottom: 16, left: 16, zIndex: 50 }}>
        <button
          onClick={() => setShowBgPicker(o => !o)}
          style={{
            background: 'rgba(0,0,0,0.6)', border: '1px solid #333',
            color: '#888', fontSize: 11, padding: '5px 10px',
            borderRadius: 4, cursor: 'pointer', fontFamily: 'inherit',
          }}
        >
          {bg.label}
        </button>
        {showBgPicker && (
          <div style={{
            position: 'absolute', bottom: '100%', left: 0, marginBottom: 6,
            background: 'rgba(10,10,14,0.97)', border: '1px solid #222',
            borderRadius: 6, padding: 6, display: 'flex', flexDirection: 'column', gap: 2,
            minWidth: 160,
          }}>
            {BACKGROUNDS.map(b => (
              <button
                key={b.id}
                onClick={() => { setBg(b); setShowBgPicker(false) }}
                style={{
                  background: b.id === bg.id ? 'rgba(255,255,255,0.08)' : 'transparent',
                  border: 'none', color: b.id === bg.id ? '#e0e0e0' : '#888',
                  fontSize: 11, padding: '5px 8px', borderRadius: 3,
                  cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                }}
              >
                {b.label}
              </button>
            ))}
          </div>
        )}
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: '48px 32px',
        maxWidth: 1300,
        margin: '0 auto',
        justifyItems: 'center',
        position: 'relative', zIndex: 1,
      }}>
        {artworks.map(art => (
          <div key={art.id} ref={el => { easelRefs.current[art.id] = el }}>
            <Easel
              artwork={art}
              owner={art.owner_id ? agentMap.get(art.owner_id) : undefined}
              agents={agentMap}
            />
          </div>
        ))}
      </div>

      {artworks.length === 0 && (
        <p style={{ textAlign: 'center', color: '#444', marginTop: 120, fontSize: 14 }}>
          The gallery is empty.
        </p>
      )}

      {/* Agent avatar layer — independent overlay above easels, scrolls with page */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 20 }}>
        {agents.map((agent, index) => {
          const ownedArt = artworks.find(a => a.owner_id === agent.id)
          const easelEl = ownedArt ? easelRefs.current[ownedArt.id] : null
          if (!easelEl || !gridRef.current) return null
          const easelRect = easelEl.getBoundingClientRect()
          const containerRect = gridRef.current.getBoundingClientRect()
          return (
            <AgentAvatar
              key={agent.id}
              agent={agent}
              index={index}
              x={easelRect.left - containerRect.left + easelRect.width * 0.65}
              y={easelRect.bottom - containerRect.top - 60}
            />
          )
        })}
      </div>

      <Sidebar agents={agents} ledger={ledger} />
    </div>
  )
}
