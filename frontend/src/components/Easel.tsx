import { useState, useEffect, useRef } from 'react'
import PixelCanvas from './PixelCanvas'
import type { Artwork, Agent, LedgerEntry } from '../types'

interface EaselProps {
  artwork: Artwork
  owner: Agent | undefined
  agents: Map<string, Agent>
}

const FRAME_PX = 214

export default function Easel({ artwork, owner, agents }: EaselProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [history, setHistory] = useState<LedgerEntry[] | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!showTooltip) return
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowTooltip(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showTooltip])

  const frameColor = owner?.color || '#888888'

  const handleClick = async () => {
    if (!showTooltip) {
      try {
        const res = await fetch(`/api/artworks/${artwork.id}/history`)
        setHistory(await res.json())
      } catch { setHistory([]) }
    }
    setShowTooltip(!showTooltip)
  }

  const W = FRAME_PX + 16
  const legSpread = 28
  const legHeight = 72
  const crossbarY = 52

  return (
    <div ref={containerRef} style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div onClick={handleClick} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

        {/* Framed artwork */}
        <div style={{
          border: `5px solid ${frameColor}`,
          padding: 3,
          background: '#1a1a1a',
          boxShadow: `0 0 18px ${frameColor}55, 0 6px 32px rgba(0,0,0,0.8)`,
          position: 'relative', zIndex: 1,
        }}>
          <PixelCanvas pixelData={artwork.pixel_data} scale={2} />
          {/* Title plate */}
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0,
            background: 'rgba(0,0,0,0.72)',
            borderTop: `1px solid ${frameColor}44`,
            padding: '3px 6px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{
              fontSize: 18, color: '#ccc', fontWeight: 'bold',
              textTransform: 'uppercase', letterSpacing: 0.8,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              flex: 1,
            }}>
              {artwork.title}
            </span>
            {artwork.is_listed && artwork.listed_price != null && (
              <span style={{ fontSize: 11, color: '#ffd700', marginLeft: 6, flexShrink: 0 }}>
                {artwork.listed_price} kr
              </span>
            )}
          </div>
        </div>

        {/* SVG easel legs */}
        <svg
          width={W + legSpread * 2}
          height={legHeight}
          viewBox={`0 0 ${W + legSpread * 2} ${legHeight}`}
          style={{ display: 'block', marginTop: -2 }}
        >
          <line x1={W / 2 + legSpread} y1={0} x2={W / 2 + legSpread} y2={legHeight}
            stroke={frameColor} strokeWidth="2.5" strokeOpacity="0.45" />
          <line x1={legSpread + W * 0.2} y1={0} x2={4} y2={legHeight}
            stroke={frameColor} strokeWidth="3" strokeOpacity="0.7" />
          <line x1={legSpread + W * 0.8} y1={0} x2={W + legSpread * 2 - 4} y2={legHeight}
            stroke={frameColor} strokeWidth="3" strokeOpacity="0.7" />
          <line x1={legSpread * 0.3 + W * 0.05} y1={crossbarY} x2={legSpread * 1.7 + W * 0.95} y2={crossbarY}
            stroke={frameColor} strokeWidth="2" strokeOpacity="0.35" />
          <rect x={legSpread * 0.6} y={0} width={W + legSpread * 0.8} height={5}
            fill={frameColor} fillOpacity="0.25" rx="1" />
        </svg>
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div
          onClick={e => e.stopPropagation()}
          style={{
            position: 'absolute', top: 0, left: '100%', marginLeft: 12,
            zIndex: 100, background: '#141414ee',
            border: `1px solid ${frameColor}44`, borderRadius: 6,
            padding: 14, minWidth: 240, maxWidth: 300,
            boxShadow: `0 8px 32px rgba(0,0,0,0.85)`,
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ marginBottom: 8 }}>
            <span style={{ fontWeight: 'bold', fontSize: 13, color: '#e0e0e0' }}>{artwork.title}</span>
          </div>
          <p style={{ fontSize: 11, color: '#999', marginBottom: 10, lineHeight: 1.4, fontStyle: 'italic' }}>
            "{artwork.story}"
          </p>
          <div style={{ fontSize: 10, color: '#777', marginBottom: 3 }}>
            Creator: <span style={{ color: '#bbb' }}>{agents.get(artwork.creator_id)?.name || 'unknown'}</span>
          </div>
          <div style={{ fontSize: 10, color: '#777', marginBottom: 8 }}>
            Owner: <span style={{ color: frameColor }}>{owner?.name || 'unknown'}</span>
          </div>
          {artwork.is_listed && artwork.listed_price != null && (
            <div style={{ fontSize: 12, color: '#ffd700', marginBottom: 8 }}>Listed: {artwork.listed_price} kr</div>
          )}
          {history && history.length > 0 && (
            <div>
              <div style={{ fontSize: 9, color: '#555', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Provenance</div>
              <div style={{ maxHeight: 150, overflowY: 'auto' }}>
                {history.map(entry => {
                  const entryAgent = agents.get(entry.owner_id)
                  return (
                    <div key={entry.id} style={{
                      fontSize: 10, padding: '3px 0', borderBottom: '1px solid #222',
                      display: 'flex', justifyContent: 'space-between',
                    }}>
                      <span style={{ color: entry.status === 'SOLD' ? '#4aff7a' : entry.status === 'LISTED' ? '#ffd700' : '#888', width: 40, fontSize: 9 }}>
                        {entry.status}
                      </span>
                      <span style={{ color: '#aaa', flex: 1, textAlign: 'center' }}>{entry.price} kr</span>
                      <span style={{ color: entryAgent?.color || '#888' }}>{entryAgent?.name || '...'}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
