export interface Background {
  id: string
  label: string
  url: string | null
  css: string  // fallback / overlay gradient
  floor: string
  floorBorder: string
}

export const BACKGROUNDS: Background[] = [
  {
    id: 'dungeon',
    label: '🏰 Dungeon',
    url: 'https://opengameart.org/sites/default/files/preview_279.png',
    css: 'radial-gradient(ellipse at 50% 30%, #1a0e2e 0%, #0d0a1a 60%, #060408 100%)',
    floor: 'linear-gradient(180deg, #1a1008 0%, #0e0a04 100%)',
    floorBorder: '#3a2a10',
  },
  {
    id: 'medieval',
    label: '⚔️ Medieval',
    url: null,
    css: 'radial-gradient(ellipse at 50% 20%, #2a1a0a 0%, #1a1005 50%, #0a0803 100%)',
    floor: 'linear-gradient(180deg, #2a1a08 0%, #1a1005 100%)',
    floorBorder: '#6b4c1e',
  },
  {
    id: 'wizard',
    label: '🔮 Wizard Tower',
    url: null,
    css: 'radial-gradient(ellipse at 40% 20%, #1a0a3a 0%, #0d0520 60%, #050210 100%)',
    floor: 'linear-gradient(180deg, #1a0a2a 0%, #0d0518 100%)',
    floorBorder: '#6a2aaa',
  },
  {
    id: 'farm',
    label: '🌾 Farm',
    url: null,
    css: 'linear-gradient(180deg, #1a3a1a 0%, #0d2010 50%, #060e08 100%)',
    floor: 'linear-gradient(180deg, #2a3a10 0%, #1a2808 100%)',
    floorBorder: '#4a6a1a',
  },
  {
    id: 'modern',
    label: '🏙️ Modern Gallery',
    url: null,
    css: 'linear-gradient(180deg, #0a0a0f 0%, #111118 50%, #0a0a0f 100%)',
    floor: 'linear-gradient(180deg, #1a1a22 0%, #111118 100%)',
    floorBorder: '#2a2a3a',
  },
  {
    id: 'space',
    label: '🚀 Space Station',
    url: null,
    css: 'radial-gradient(ellipse at 30% 20%, #001a3a 0%, #000a1a 60%, #000005 100%)',
    floor: 'linear-gradient(180deg, #001020 0%, #000810 100%)',
    floorBorder: '#003a6a',
  },
  {
    id: 'tavern',
    label: '🍺 Tavern',
    url: null,
    css: 'radial-gradient(ellipse at 50% 30%, #2a1505 0%, #1a0e03 60%, #0a0802 100%)',
    floor: 'linear-gradient(180deg, #3a2010 0%, #2a1808 100%)',
    floorBorder: '#8b5e2a',
  },
  {
    id: 'underwater',
    label: '🌊 Underwater',
    url: null,
    css: 'radial-gradient(ellipse at 50% 0%, #003a4a 0%, #001a2a 60%, #000a10 100%)',
    floor: 'linear-gradient(180deg, #002a3a 0%, #001520 100%)',
    floorBorder: '#005a7a',
  },
]
