import { describe, expect, test } from 'vitest'
import { cellFromCoordinate, coordinateFromCell, parseTerrainMeta } from './terrain'

const valid = {
  id: 'slope', name: 'Malla', sourceLayer: 'ctx-dem-slope', sourceImage: 'maps/a.jpg',
  grid: 'terrain/a.png', units: 'relative-index-0-255', extent: [-50, -50, 50, 50],
  width: 10, height: 10, resolution: { x: 10, y: 10 }, origin: 'top-left', notes: [], generated: '2026-01-01',
}

describe('ficha de la malla de pendientes', () => {
  test('acepta una ficha completa', () => {
    expect(parseTerrainMeta(valid).width).toBe(10)
  })

  test('rechaza fichas incompletas o incoherentes', () => {
    expect(() => parseTerrainMeta(null)).toThrow(/ficha/i)
    expect(() => parseTerrainMeta({ ...valid, extent: [0, 0, 0, 10] })).toThrow(/extensión/i)
    expect(() => parseTerrainMeta({ ...valid, width: 0 })).toThrow(/dimensiones/i)
    expect(() => parseTerrainMeta({ ...valid, resolution: { x: 0, y: 10 } })).toThrow(/resolución/i)
    expect(() => parseTerrainMeta({ ...valid, grid: 'terrain/a.json' })).toThrow(/archivo/i)
  })

  test('la esquina superior izquierda es la primera celda y el exterior devuelve -1', () => {
    const meta = parseTerrainMeta(valid)
    expect(cellFromCoordinate(meta, [-45, 45])).toBe(0)
    expect(cellFromCoordinate(meta, [45, -45])).toBe(99)
    expect(cellFromCoordinate(meta, [60, 0])).toBe(-1)
    const centre = coordinateFromCell(meta, 0)
    expect(centre).toEqual([-45, 45])
  })
})