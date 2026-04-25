import { useState } from 'react'
import type { Agent, LedgerEntry } from '../types'

interface SidebarProps {
  agents: Agent[]
  ledger: LedgerEntry[]
}

export default function Sidebar({ agents, ledger }: SidebarProps) {
  const [open, setOpen] = useState(false)
  const agentMap = new Map(agents.map(a => [a.id, a]))

  return (
    <>
      {/* Toggle tab */}
      <div
        onClick={() => setOpen(!open)}
        style={{
          position: 'fixed', right: open ? 320 : 0, top: '50%',
          transform: 'translateY(-50%)',
          background: '#1a1a1aee', border: '1px solid #333',
          borderRight: open ? 'none' : '1px solid #333',
          borderRadius: open ? '6px 0 0 6px' : '6px 0 0 6px',
          padding: '12px 8px', cursor: 'pointer',
          zIndex: 200, writingMode: 'vertical-rl',
          fontSize: 11, color: '#888', letterSpacing: 1,
          transition: 'right 0.3s ease',
        }}
      >
        {open ? 'CLOSE' : 'LEDGER'}
      </div>

      {/* Panel */}
      <div style={{
        position: 'fixed', right: open ? 0 : -320, top: 0, bottom: 0,
        width: 320, background: '#0d0d0dee',
        borderLeft: '1px solid #222',
        zIndex: 199, transition: 'right 0.3s ease',
        display: 'flex', flexDirection: 'column',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ padding: '16px 16px 8px', borderBottom: '1px solid #222' }}>
          <h3 style={{ margin: 0, fontSize: 14, color: '#e0e0e0', letterSpacing: 1 }}>TRANSACTION LEDGER</h3>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
          {ledger.length === 0 && <p style={{ color: '#555', fontSize: 12, padding: 8 }}>No transactions yet.</p>}
          {ledger.map((entry) => {
            const agent = agentMap.get(entry.owner_id)
            return (
              <div key={entry.id} style={{
                padding: '8px 10px', borderBottom: '1px solid #1a1a1a',
                fontSize: 11,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                  <span style={{
                    color: entry.status === 'SOLD' ? '#4aff7a'
                      : entry.status === 'LISTED' ? '#ffd700'
                      : '#4a9eff',
                    fontWeight: 'bold',
                  }}>
                    {entry.status}
                  </span>
                  <span style={{ color: '#aaa' }}>{entry.price} kr</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: `#${agent?.color || '888'}` }}>
                    {agent?.name || entry.owner_id.slice(0, 8)}
                  </span>
                  <span style={{ color: '#555', fontSize: 10 }}>
                    #{entry.id}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Agent summary at bottom */}
        <div style={{ borderTop: '1px solid #222', padding: 12 }}>
          <div style={{ fontSize: 10, color: '#666', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>Agents</div>
          {agents.sort((a, b) => b.coins - a.coins).map(a => (
            <div key={a.id} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '3px 0', fontSize: 11,
            }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: `#${a.color}` }} />
              <span style={{ flex: 1, color: '#ccc' }}>{a.name}</span>
              <span style={{ color: '#888' }}>{a.coins} kr</span>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
