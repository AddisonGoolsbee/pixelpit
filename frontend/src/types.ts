export type PixelGrid = string[][]

export interface Agent {
  id: string
  name: string
  color: string
  coins: number
}

export interface Artwork {
  id: string
  title: string
  pixel_data: PixelGrid
  story: string
  creator_id: string
  owner_id: string | null
  listed_price: number | null
  is_listed: boolean
}

export interface LedgerEntry {
  id: number
  status: 'JOINED' | 'LISTED' | 'SOLD'
  owner_id: string
  price: number
  is_listed: boolean
  created_at: number
}

export interface LeaderboardAgent {
  rank: number
  name: string
  coins: number
  id: string
}
