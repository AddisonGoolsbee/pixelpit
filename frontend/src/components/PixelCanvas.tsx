import { useRef, useEffect } from 'react'

interface PixelCanvasProps {
  pixelData: string[][]
  scale?: number
}

export default function PixelCanvas({ pixelData, scale = 2 }: PixelCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!pixelData || !pixelData.length) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const rows = pixelData.length
    const cols = pixelData[0]?.length || 0

    canvas.width = cols * scale
    canvas.height = rows * scale

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const color = pixelData[y]?.[x] || '000000'
        ctx.fillStyle = `#${color}`
        ctx.fillRect(x * scale, y * scale, scale, scale)
      }
    }
  }, [pixelData, scale])

  return <canvas ref={canvasRef} style={{ imageRendering: 'pixelated', borderRadius: 4 }} />
}
