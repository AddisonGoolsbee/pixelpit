type PixelGrid = string[][]

interface Agent {
  id: string
  name: string
  coins: number
}

interface Artwork {
  id: string
  artwork_id?: string
  title: string
  pixel_data: PixelGrid
  story: string
  creator_id: string
  owner_id: string | null
  listed_price: number | null
  is_listed?: boolean
  highest_sale_price?: number
}

interface LeaderboardAgent {
  rank: number
  name: string
  coins: number
  id: string
}

interface TopArtwork {
  artwork_id: string
  title: string
  pixel_data: PixelGrid
  highest_sale_price: number
  creator_id: string
  current_owner_id: string | null
}
