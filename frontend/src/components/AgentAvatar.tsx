import { useEffect, useRef, useState } from 'react'
import type { Agent } from '../types'

interface AgentAvatarProps {
  agent: Agent
  index: number
  x: number
  y: number
}

const FRAME_COUNT = 7
const FPS = 6

const imgCache: Record<string, HTMLImageElement> = {}

function loadImage(src: string): Promise<HTMLImageElement> {
  if (imgCache[src]) return Promise.resolve(imgCache[src])
  return new Promise(resolve => {
    const img = new Image()
    img.onload = () => { imgCache[src] = img; resolve(img) }
    img.src = src
  })
}

function agentRandom(id: string): number {
  let hash = 0
  for (const c of id) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return (hash % 1000) / 1000
}

export default function AgentAvatar({ agent, x, y }: AgentAvatarProps) {
  const [frame, setFrame] = useState(0)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const flipped = agentRandom(agent.id) > 0.5

  useEffect(() => {
    const interval = setInterval(() => setFrame(f => (f + 1) % FRAME_COUNT), 1000 / FPS)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!

    Promise.all([
      loadImage(`/avatars/walk_${frame}.png`),
      loadImage(`/avatars/walk_${frame}_mask.png`),
    ]).then(([base, mask]) => {
      ctx.clearRect(0, 0, 64, 64)

      // Draw base sprite (skin, hair, boots)
      ctx.drawImage(base, 0, 0, 64, 64)

      // Build colored clothing on offscreen canvas
      const off = document.createElement('canvas')
      off.width = off.height = 64
      const octx = off.getContext('2d')!
      // Draw mask (white clothing shape)
      octx.drawImage(mask, 0, 0, 64, 64)
      // Fill agent color, clipped to mask shape
      octx.globalCompositeOperation = 'source-in'
      octx.fillStyle = agent.color
      octx.fillRect(0, 0, 64, 64)

      // Composite colored clothing over base
      ctx.drawImage(off, 0, 0)
    })
  }, [frame, agent.color])

  return (
    <div style={{
      position: 'absolute', left: x, top: y,
      transform: 'translateX(-50%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      pointerEvents: 'none',
      transition: 'left 1.8s cubic-bezier(0.4,0,0.2,1), top 1.8s cubic-bezier(0.4,0,0.2,1)',
    }}>
      <div style={{ transform: flipped ? 'scaleX(-1)' : undefined }}>
        <canvas ref={canvasRef} width={64} height={64}
          style={{ imageRendering: 'pixelated', display: 'block', filter: 'drop-shadow(0 3px 6px rgba(0,0,0,0.8))' }}
        />
      </div>
      <span style={{
        fontSize: 9, color: '#ddd', marginTop: 2,
        whiteSpace: 'nowrap', textShadow: '0 1px 4px rgba(0,0,0,0.9)',
        background: 'rgba(0,0,0,0.5)', padding: '1px 4px', borderRadius: 2,
      }}>
        {agent.name}
      </span>
    </div>
  )
}
