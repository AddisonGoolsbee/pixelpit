import { useState } from 'react'
import PixelCanvas from './PixelCanvas'
import type { Artwork, Agent, LedgerEntry } from '../types'

interface EaselProps {
  artwork: Artwork
  owner: Agent | undefined
  agents: Map<string, Agent>
}

export default function Easel({ artwork, owner, agents }: EaselProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [history, setHistory] = useState<LedgerEntry[] | null>(null)

  const frameColor = owner?.color || 'FFFFFF'

  const handleClick = async () => {
    if (!showTooltip) {
      try {
        const res = await fetch(`/api/artworks/${artwork.id}/history`)
        setHistory(await res.json())
      } catch { setHistory([]) }
    }
    setShowTooltip(!showTooltip)
  }

  return (
    <div style={{ position: 'relative' }}>
      <div
        onClick={handleClick}
        style={{
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Frame with colored border */}
        <div style={{
          border: `5px solid #${frameColor}`,
          padding: 3,
          background: '#222',
          boxShadow: `0 0 16px #${frameColor}22, 0 4px 24px rgba(0,0,0,0.7)`,
        }}>
          <PixelCanvas pixelData={artwork.pixel_data} scale={2} />
        </div>

        {/* Title + price below frame */}
        <div style={{
          marginTop: 8,
          textAlign: 'center',
          maxWidth: 210,
        }}>
          <div style={{
            fontSize: 11, color: '#ccc', fontWeight: 'bold',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            textTransform: 'uppercase', letterSpacing: 0.5,
          }}>
            {artwork.title}
          </div>
          {artwork.is_listed && artwork.listed_price != null && (
            <div style={{ fontSize: 10, color: '#ffd700', marginTop: 2 }}>{artwork.listed_price} kr</div>
          )}
        </div>

        {/* Owner figure below */}
        {owner && (
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {/* Head */}
            <div style={{
              width: 12, height: 12, borderRadius: '50%',
              background: `#${owner.color}`,
              boxShadow: `0 0 6px #${owner.color}44`,
            }} />
            {/* Body */}
            <div style={{
              width: 8, height: 14,
              background: `#${owner.color}99`,
              borderRadius: '2px 2px 0 0',
              marginTop: 1,
            }} />
            {/* Legs */}
            <div style={{ display: 'flex', gap: 2 }}>
              <div style={{ width: 3, height: 8, background: `#${owner.color}55` }} />
              <div style={{ width: 3, height: 8, background: `#${owner.color}55` }} />
            </div>
            <span style={{ fontSize: 8, color: '#888', marginTop: 2 }}>{owner.name}</span>
          </div>
        )}
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div
          onClick={e => e.stopPropagation()}
          style={{
            position: 'absolute',
            top: 0,
            left: '100%',
            marginLeft: 10,
            zIndex: 100,
            background: '#1a1a1aee',
            border: `1px solid #${frameColor}44`,
            borderRadius: 6,
            padding: 14,
            minWidth: 240,
            maxWidth: 300,
            boxShadow: `0 8px 32px rgba(0,0,0,0.8)`,
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontWeight: 'bold', fontSize: 13, color: '#e0e0e0' }}>{artwork.title}</span>
            <button
              onClick={() => setShowTooltip(false)}
              style={{ background: 'none', border: 'none', color: '#555', cursor: 'pointer', fontSize: 14 }}
            >x</button>
          </div>

          <p style={{ fontSize: 11, color: '#999', marginBottom: 10, lineHeight: 1.4, fontStyle: 'italic' }}>
            "{artwork.story}"
          </p>

          <div style={{ fontSize: 10, color: '#777', marginBottom: 3 }}>
            Creator: <span style={{ color: '#bbb' }}>{agents.get(artwork.creator_id)?.name || 'unknown'}</span>
          </div>
          <div style={{ fontSize: 10, color: '#777', marginBottom: 8 }}>
            Owner: <span style={{ color: `#${frameColor}` }}>{owner?.name || 'unknown'}</span>
          </div>

          {artwork.is_listed && artwork.listed_price != null && (
            <div style={{ fontSize: 12, color: '#ffd700', marginBottom: 8 }}>Listed: {artwork.listed_price} kr</div>
          )}

          {history && history.length > 0 && (
            <div>
              <div style={{ fontSize: 9, color: '#555', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Provenance</div>
              <div style={{ maxHeight: 150, overflowY: 'auto' }}>
                {history.map((entry) => {
                  const entryAgent = agents.get(entry.owner_id)
                  return (
                    <div key={entry.id} style={{
                      fontSize: 10, padding: '3px 0',
                      borderBottom: '1px solid #222',
                      display: 'flex', justifyContent: 'space-between',
                    }}>
                      <span style={{
                        color: entry.status === 'SOLD' ? '#4aff7a' : entry.status === 'LISTED' ? '#ffd700' : '#888',
                        width: 40, fontSize: 9,
                      }}>
                        {entry.status}
                      </span>
                      <span style={{ color: '#aaa', flex: 1, textAlign: 'center' }}>{entry.price} kr</span>
                      <span style={{ color: `#${entryAgent?.color || '888'}` }}>
                        {entryAgent?.name || '...'}
                      </span>
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
