type PixelGrid = string[][]

interface Agent {
  id: number
  name: string
  personality: string
  coins: number
  face_data: PixelGrid
}

interface Artwork {
  id: number
  artwork_id?: number
  title: string
  pixel_data: PixelGrid
  story: string
  creator_id: number
  owner_id: number
  creation_cost: number
  listed_price: number | null
  created_at_round: number
  highest_sale_price?: number
}

interface LeaderboardAgent {
  rank: number
  name: string
  coins: number
  id: number
}

interface TopArtwork {
  artwork_id: number
  title: string
  pixel_data: PixelGrid
  highest_sale_price: number
  creator_id: number
  current_owner_id: number
}
