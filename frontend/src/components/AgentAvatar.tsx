import type { Agent } from '../types'

interface AgentAvatarProps {
  agent: Agent
  x: number
  y: number
}

export default function AgentAvatar({ agent, x, y }: AgentAvatarProps) {
  return (
    <div style={{
      position: 'absolute',
      left: x,
      top: y,
      transform: 'translateX(-50%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      pointerEvents: 'none',
      filter: `drop-shadow(0 3px 8px rgba(0,0,0,0.9))`,
      transition: 'left 1.8s cubic-bezier(0.4,0,0.2,1), top 1.8s cubic-bezier(0.4,0,0.2,1)',
    }}>
      {/* Head */}
      <div style={{ width: 20, height: 20, borderRadius: '50%', background: agent.color, boxShadow: `0 0 8px ${agent.color}` }} />
      {/* Body */}
      <div style={{ width: 14, height: 22, background: agent.color + 'cc', borderRadius: '3px 3px 0 0', marginTop: 1 }} />
      {/* Legs */}
      <div style={{ display: 'flex', gap: 3 }}>
        <div style={{ width: 5, height: 12, background: agent.color + '88' }} />
        <div style={{ width: 5, height: 12, background: agent.color + '88' }} />
      </div>
      <span style={{ fontSize: 9, color: '#ddd', marginTop: 3, whiteSpace: 'nowrap', textShadow: '0 1px 4px rgba(0,0,0,0.9)' }}>
        {agent.name}
      </span>
    </div>
  )
}
