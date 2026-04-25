import { useState, useEffect } from 'react'
import PixelCanvas from '../components/PixelCanvas'
import type { Artwork, TopArtwork } from '../types'

export default function Gallery() {
  const [artworks, setArtworks] = useState<(Artwork | TopArtwork)[]>([])
  const [tab, setTab] = useState('all')

  const fetchAll = () => fetch('/api/artworks/').then(r => r.json()).then(setArtworks)
  const fetchTop = () => fetch('/api/artworks/top').then(r => r.json()).then(setArtworks)

  useEffect(() => {
    if (tab === 'all') fetchAll()
    else fetchTop()
  }, [tab])

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button onClick={() => setTab('all')} style={tabBtn(tab === 'all')}>All Art</button>
        <button onClick={() => setTab('top')} style={tabBtn(tab === 'top')}>Top Sales</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16 }}>
        {artworks.map((a) => {
          const id = 'id' in a ? a.id : a.artwork_id
          const highestSale = 'highest_sale_price' in a ? a.highest_sale_price : undefined
          const listedPrice = 'listed_price' in a ? a.listed_price : undefined
          return (
            <div key={id} style={{
              background: '#111', borderRadius: 8, padding: 12, textAlign: 'center',
            }}>
              <PixelCanvas pixelData={a.pixel_data} scale={2} />
              <p style={{ marginTop: 8, fontWeight: 'bold' }}>{a.title}</p>
              {highestSale != null && (
                <p style={{ color: '#ffd700' }}>Sold for {highestSale} coins</p>
              )}
              {listedPrice != null && (
                <p style={{ color: '#4aff7a' }}>Listed: {listedPrice} coins</p>
              )}
              <p style={{ color: '#888', fontSize: 12 }}>Creator #{a.creator_id}</p>
            </div>
          )
        })}
        {artworks.length === 0 && <p style={{ color: '#666' }}>No artworks yet.</p>}
      </div>
    </div>
  )
}

const tabBtn = (active: boolean): React.CSSProperties => ({
  padding: '6px 14px', border: 'none', borderRadius: 4, cursor: 'pointer',
  background: active ? '#333' : 'transparent', color: '#e0e0e0', fontFamily: 'inherit',
})
