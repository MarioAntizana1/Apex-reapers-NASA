import { describe, expect, test } from 'vitest'
import {
  climbCost, DEFAULT_DESCENT_FACTOR, measurePath, planRoute, simplifyPath, smoothPath, slopeCost, straightAscent,
  type PlanOptions, type RoutePoint,
} from './planner'
import { cellFromCoordinate, coordinateFromCell, type TerrainField, type TerrainMeta } from './terrain'

const RESOLUTION = 10
const METRES_PER_INDEX = 10

function makeGrid(
  width: number,
  height: number,
  severityAt: (col: number, row: number) => number,
  elevationAt?: (col: number, row: number) => number,
): TerrainField {
  const meta: TerrainMeta = {
    id: 'test', name: 'Prueba', extent: [0, 0, width * RESOLUTION, height * RESOLUTION],
    width, height, resolution: { x: RESOLUTION, y: RESOLUTION }, origin: 'top-left', notes: [], generated: '2026-01-01',
    slope: { grid: 'terrain/test.png', sourceLayer: 'test', sourceImage: 'test.jpg', units: 'relative-index-0-255' },
    elevation: elevationAt
      ? { grid: 'terrain/elev.png', sourceLayer: 'dem', sourceImage: 'dem.png', units: 'relative-index-0-255', metresPerIndex: METRES_PER_INDEX }
      : null,
  }
  const severity = new Uint8Array(width * height)
  const elevation = elevationAt ? new Uint8Array(width * height) : null
  for (let row = 0; row < height; row += 1) {
    for (let col = 0; col < width; col += 1) {
      severity[row * width + col] = severityAt(col, row)
      if (elevation && elevationAt) elevation[row * width + col] = elevationAt(col, row)
    }
  }
  return { meta, severity, elevation, metresPerIndex: elevationAt ? METRES_PER_INDEX : 0 }
}

function cellCentre(meta: TerrainMeta, col: number, row: number): RoutePoint {
  return coordinateFromCell(meta, row * meta.width + col)
}

const flat: PlanOptions = { maxSeverity: 178, slopePenalty: 6 }

describe('planRoute en terreno liso', () => {
  test('la ruta mide lo mismo que la línea recta y no paga pendiente', () => {
    const field = makeGrid(20, 20, () => 0)
    const meta = field.meta
    const from = cellCentre(meta, 2, 10)
    const to = cellCentre(meta, 17, 10)
    const plan = planRoute(field, [from, to], flat)

    expect(plan.ok).toBe(true)
    expect(plan.legs).toHaveLength(1)
    expect(plan.distance).toBeCloseTo(plan.straight, 0)
    expect(plan.effort).toBeCloseTo(1, 2)
    expect(plan.maxSeverity).toBe(0)
    expect(plan.failedLegs).toEqual([])
    expect(plan.visited).toBeGreaterThan(0)
    expect(Number.isFinite(plan.elapsed)).toBe(true)
  })

  test('un punto de destino repetido no rompe el cálculo', () => {
    const field = makeGrid(8, 8, () => 0)
    const point = cellCentre(field.meta, 3, 3)
    const plan = planRoute(field, [point, point], flat)
    expect(plan.ok).toBe(true)
    expect(plan.distance).toBe(0)
  })

  test('encadena varios tramos y suma sus distancias', () => {
    const field = makeGrid(20, 20, () => 0)
    const meta = field.meta
    const points = [cellCentre(meta, 1, 1), cellCentre(meta, 10, 1), cellCentre(meta, 10, 12)]
    const plan = planRoute(field, points, flat)
    expect(plan.ok).toBe(true)
    expect(plan.legs).toHaveLength(2)
    expect(plan.distance).toBeCloseTo(plan.legs[0].distance + plan.legs[1].distance, 5)
    expect(plan.straight).toBeGreaterThan(0)
  })
})

describe('planRoute y las pendientes', () => {
  test('rodea una franja inclinada en lugar de cruzarla', () => {
    const severityAt = (col: number, row: number) => (col === 10 && row >= 4 && row <= 15 ? 240 : 0)
    const field = makeGrid(21, 20, severityAt)
    const from = cellCentre(field.meta, 7, 10)
    const to = cellCentre(field.meta, 13, 10)

    const steep = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 12 })
    expect(steep.ok).toBe(true)
    expect(steep.maxSeverity).toBeLessThan(240)
    expect(steep.distance).toBeGreaterThan(steep.straight)

    const carefree = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 0 })
    expect(carefree.maxSeverity).toBe(240)
    expect(carefree.distance).toBeCloseTo(carefree.straight, 0)
  })

  test('una pared intransitable bloquea el paso salvo que se suba la tolerancia', () => {
    const severityAt = (col: number) => (col === 10 ? 255 : 0)
    const field = makeGrid(21, 20, severityAt)
    const from = cellCentre(field.meta, 4, 10)
    const to = cellCentre(field.meta, 16, 10)

    const blocked = planRoute(field, [from, to], { maxSeverity: 178, slopePenalty: 6 })
    expect(blocked.ok).toBe(false)
    expect(blocked.failedLegs).toEqual([0])
    expect(blocked.legs[0].reason).toMatch(/no hay paso/i)

    const open = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 6 })
    expect(open.ok).toBe(true)
    expect(open.maxSeverity).toBe(255)
  })

  test('el índice de pendiente encarece cada metro de forma cuadrática', () => {
    expect(slopeCost(0, 6)).toBe(1)
    expect(slopeCost(255, 6)).toBeCloseTo(7, 5)
    expect(slopeCost(128, 6)).toBeCloseTo(1 + 6 * (128 / 255) ** 2, 5)
    expect(slopeCost(255, 0)).toBe(1)
  })
})

describe('planRoute y el desnivel', () => {
  // Colina cónica de radio 12 celdas y 255 puntos de altura (2.550 m) en la cima.
  const hill = (width: number) => (col: number, row: number) => {
    const cx = (width - 1) / 2
    const cy = 20
    const distance = Math.hypot(col - cx, row - cy)
    return Math.max(0, Math.round(255 * (1 - distance / 12)))
  }

  test('subir cuesta más que bajar', () => {
    expect(climbCost(0, 4)).toBe(0)
    expect(climbCost(100, 4)).toBe(400)
    expect(climbCost(-100, 4)).toBeCloseTo(400 * DEFAULT_DESCENT_FACTOR, 6)
    expect(climbCost(100, 0)).toBe(0)
  })

  test('rodea la colina en vez de coronarla', () => {
    const field = makeGrid(41, 41, () => 0, hill(41))
    const from = cellCentre(field.meta, 2, 20)
    const to = cellCentre(field.meta, 38, 20)

    const flatOnly = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 0, climbPenalty: 0 })
    expect(flatOnly.distance).toBeCloseTo(flatOnly.straight, 0)
    expect(flatOnly.ascent).toBeGreaterThan(2000)

    const climbAware = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 0, climbPenalty: 6 })
    expect(climbAware.ok).toBe(true)
    // Rodea la falda: sube mucho menos que la línea recta, que corona la cima.
    expect(climbAware.ascent).toBeLessThan(climbAware.straightAscent * 0.3)
    expect(climbAware.distance).toBeGreaterThan(climbAware.straight)
  })

  test('el desnivel de la ruta se compara con el de la línea recta', () => {
    const field = makeGrid(41, 41, () => 0, hill(41))
    const from = cellCentre(field.meta, 2, 20)
    const to = cellCentre(field.meta, 38, 20)
    const plan = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 0, climbPenalty: 6 })

    expect(plan.straightAscent).toBeGreaterThan(2000)
    expect(plan.ascent).toBeLessThan(plan.straightAscent)
    expect(plan.descent).toBeCloseTo(plan.ascent, 0)
  })

  test('sin malla de altura el desnivel es cero y nada cambia', () => {
    const field = makeGrid(21, 20, () => 0)
    const from = cellCentre(field.meta, 4, 10)
    const to = cellCentre(field.meta, 16, 10)
    const plan = planRoute(field, [from, to], { maxSeverity: 255, slopePenalty: 6, climbPenalty: 6 })
    expect(plan.ascent).toBe(0)
    expect(plan.straightAscent).toBe(0)
    expect(plan.distance).toBeCloseTo(plan.straight, 0)
  })

  test('straightAscent acumula solo los tramos de subida', () => {
    const field = makeGrid(21, 10, () => 0, col => (col < 10 ? col * 10 : 100))
    expect(straightAscent(field, [0, 50], [100, 50])).toBeCloseTo(100 * METRES_PER_INDEX, 0)
  })
})

describe('planRoute y los límites del mapa', () => {
  test('un punto fuera de la malla se informa como tramo fallido', () => {
    const field = makeGrid(10, 10, () => 0)
    const plan = planRoute(field, [[-40, 50], cellCentre(field.meta, 5, 5)], flat)
    expect(plan.ok).toBe(false)
    expect(plan.failedLegs).toEqual([0])
    expect(plan.legs[0].reason).toMatch(/fuera de la malla/i)
  })

  test('un extremo sobre terreno intransitable se acerca al borde transitable', () => {
    const severityAt = (col: number, row: number) => (col === 5 && row === 5 ? 255 : 0)
    const field = makeGrid(11, 11, severityAt)
    const blocked = cellCentre(field.meta, 5, 5)
    const plan = planRoute(field, [blocked, cellCentre(field.meta, 9, 5)], flat)
    expect(plan.ok).toBe(true)
    expect(plan.legs[0].snapped).toBeGreaterThan(0)
    expect(plan.maxSeverity).toBe(0)
  })

  test('sin ruta posible y sin límite alcanzado informa el motivo', () => {
    const field = makeGrid(5, 5, () => 0)
    const plan = planRoute(field, [cellCentre(field.meta, 1, 1), cellCentre(field.meta, 3, 3)], flat, 1)
    expect(plan.ok).toBe(false)
    expect(plan.truncated).toBe(true)
    expect(plan.legs[0].reason).toMatch(/límite de celdas/i)
  })
})

describe('utilidades del trazado', () => {
  test('simplifica puntos alineados y conserva los extremos', () => {
    const path: RoutePoint[] = [[0, 0], [10, 0], [20, 0], [30, 0], [30, 10]]
    const simplified = simplifyPath(path, 1)
    expect(simplified).toEqual([[0, 0], [30, 0], [30, 10]])
    expect(simplifyPath([[0, 0], [1, 1]], 1)).toHaveLength(2)
  })

  test('suaviza el trazado sin mover los extremos', () => {
    const path: RoutePoint[] = [[0, 0], [10, 10], [20, 0], [30, 10]]
    const smooth = smoothPath(path)
    expect(smooth[0]).toEqual([0, 0])
    expect(smooth[smooth.length - 1]).toEqual([30, 10])
    expect(smooth.length).toBeGreaterThan(path.length)
    expect(smoothPath([[0, 0], [1, 1]])).toHaveLength(2)
  })

  test('mide longitud y costo sobre la malla', () => {
    const field = makeGrid(20, 20, () => 0)
    const measured = measurePath(field, [[0, 50], [100, 50]], { maxSeverity: 178, slopePenalty: 6 })
    expect(measured.distance).toBeCloseTo(100, 3)
    expect(measured.cost).toBeCloseTo(100, 3)
    expect(measured.maxSeverity).toBe(0)
  })

  test('las coordenadas de celda y de punto son reversibles', () => {
    const { meta } = makeGrid(12, 9, () => 0)
    for (const [col, row] of [[0, 0], [4, 6], [11, 8]]) {
      const cell = row * meta.width + col
      expect(cellFromCoordinate(meta, coordinateFromCell(meta, cell))).toBe(cell)
    }
    expect(cellFromCoordinate(meta, [-1, 10])).toBe(-1)
  })
})
