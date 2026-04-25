import PixelCanvas from '../components/PixelCanvas'
import type { Agent } from '../types'

interface DashboardProps {
  agents: Agent[]
}

export default function Dashboard({ agents }: DashboardProps) {
  return (
    <div>
      <h2 style={{ fontSize: 20, marginBottom: 12 }}>Agents</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
        {agents.map((a) => (
          <div key={a.id} style={{
            background: '#111', borderRadius: 8, padding: 16,
            display: 'flex', gap: 12, alignItems: 'center',
          }}>
            {a.face_data && a.face_data.length > 0 && (
              <PixelCanvas pixelData={a.face_data} scale={2} />
            )}
            <div>
              <p style={{ fontWeight: 'bold' }}>{a.name}</p>
              <p style={{ color: '#4aff7a', fontSize: 14 }}>{a.coins} coins</p>
              <p style={{ color: '#888', fontSize: 12 }}>{a.personality}</p>
            </div>
          </div>
        ))}
        {agents.length === 0 && (
          <p style={{ color: '#666' }}>No agents registered yet. Connect an AI agent via MCP.</p>
        )}
      </div>
    </div>
  )
}
