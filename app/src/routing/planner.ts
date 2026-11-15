/**
 * Planificador de rutas sobre las mallas de terreno del MDE.
 *
 * A* en 8 direcciones (sin cortar esquinas) sobre celdas de ~60 m. El costo de cada
 * paso combina dos cosas:
 *
 * 1. La pendiente de la celda: `1 + penalización · (índice/255)²` por metro recorrido.
 * 2. El desnivel: cada metro que se sube se paga como `climbPenalty` metros de
 *    recorrido equivalente; bajar cuesta solo una fracción (`descentFactor`).
 *
 * Así, cuando subir una ladera cuesta más que dar el rodeo, el algoritmo rodea: la
 * decisión surge de comparar el costo total, no de una regla fija. Las celdas por
 * encima de `maxSeverity` siguen siendo intransitables.
 */

import { cellFromCoordinate, coordinateFromCell, type TerrainField } from './terrain'

export type RoutePoint = [number, number]

export interface PlanOptions {
  /** Índice 0-255 a partir del cual el terreno se considera intransitable. */
  maxSeverity: number
  /** Cuánto encarece la pendiente máxima frente a terreno liso (0 = la ignora). */
  slopePenalty: number
  /** Costo de subir un metro, en metros de recorrido equivalente (0 = ignora el desnivel). */
  climbPenalty?: number
  /** Fracción del costo de ascenso que se paga al bajar (0 = bajar es gratis). */
  descentFactor?: number
}

export const SEVERITY_PRESETS = { conservador: 102, estandar: 178, amplio: 235 } as const
export type SeverityPreset = keyof typeof SEVERITY_PRESETS

/** Coste de subida por omisión: 1 m de ascenso ≈ 4 m llanos. */
export const DEFAULT_CLIMB_PENALTY = 4
/** Bajar cuesta, pero menos que subir. */
export const DEFAULT_DESCENT_FACTOR = 0.35

export interface ElevationStats {
  /** Metros acumulados de ascenso. */
  ascent: number
  /** Metros acumulados de descenso. */
  descent: number
  /** Pendiente máxima en porcentaje aproximado. */
  maxGrade: number
  /** Ascenso acumulado de la línea recta entre los dos extremos. */
  straightAscent: number
}

export interface LegPlan extends ElevationStats {
  index: number
  ok: boolean
  from: RoutePoint
  to: RoutePoint
  path: RoutePoint[]
  distance: number
  straight: number
  cost: number
  maxSeverity: number
  /** Metros que hubo que mover el extremo para caer en terreno transitable. */
  snapped: number
  truncated: boolean
  reason?: string
}

export interface RoutePlan extends ElevationStats {
  ok: boolean
  legs: LegPlan[]
  distance: number
  straight: number
  cost: number
  /** Costo por metro: 1 = terreno liso, más alto = más pendiente acumulada. */
  effort: number
  maxSeverity: number
  truncated: boolean
  failedLegs: number[]
  visited: number
  elapsed: number
  /**
   * Ascenso del trazado que sale ignorando la altura (mismo tramo, sin coste de
   * subida). Es la referencia honesta para decidir si el rodeo compensa: la
   * línea recta puede cruzar paredes intransitables y no ser un camino real.
   */
  baselineAscent: number
  /** Distancia del trazado que ignora la altura. */
  baselineDistance: number
  /** Descenso del trazado que ignora la altura. */
  baselineDescent: number
  /** Metros de subida ahorrados frente a ignorar la altura (0 si no ahorra). */
  savedAscent: number
  /** Metros de ruta extra pagados para ahorrar esa subida. */
  detourForClimb: number
}

const NEIGHBOUR_DX = [1, -1, 0, 0, 1, 1, -1, -1]
const NEIGHBOUR_DY = [0, 0, 1, -1, 1, -1, 1, -1]
const DIAGONAL_FROM = 4
const DEFAULT_MAX_EXPANSIONS = 1_200_000
const SNAP_RADIUS = 12

export function slopeCost(severity: number, slopePenalty: number): number {
  const normalized = severity / 255
  return 1 + slopePenalty * normalized * normalized
}

/** Costo del desnivel en metros de recorrido equivalente. */
export function climbCost(deltaMetres: number, climbPenalty: number, descentFactor = DEFAULT_DESCENT_FACTOR): number {
  if (deltaMetres === 0 || climbPenalty <= 0) return 0
  return climbPenalty * (deltaMetres > 0 ? deltaMetres : -deltaMetres * descentFactor)
}

class MinHeap {
  private ids: Int32Array
  private keys: Float32Array
  private count = 0

  constructor(capacity: number) {
    this.ids = new Int32Array(Math.max(capacity, 1024))
    this.keys = new Float32Array(Math.max(capacity, 1024))
  }

  clear(): void {
    this.count = 0
  }

  push(id: number, key: number): void {
    if (this.count === this.ids.length) {
      const ids = new Int32Array(this.ids.length * 2)
      ids.set(this.ids)
      this.ids = ids
      const keys = new Float32Array(this.keys.length * 2)
      keys.set(this.keys)
      this.keys = keys
    }
    let index = this.count
    this.count += 1
    this.ids[index] = id
    this.keys[index] = key
    while (index > 0) {
      const parent = (index - 1) >> 1
      if (this.keys[parent] <= this.keys[index]) break
      this.swap(parent, index)
      index = parent
    }
  }

  pop(): number {
    const top = this.ids[0]
    this.count -= 1
    if (this.count > 0) {
      this.ids[0] = this.ids[this.count]
      this.keys[0] = this.keys[this.count]
      let index = 0
      for (;;) {
        const left = index * 2 + 1
        const right = left + 1
        let smallest = index
        if (left < this.count && this.keys[left] < this.keys[smallest]) smallest = left
        if (right < this.count && this.keys[right] < this.keys[smallest]) smallest = right
        if (smallest === index) break
        this.swap(smallest, index)
        index = smallest
      }
    }
    return top
  }

  get size(): number {
    return this.count
  }

  private swap(a: number, b: number): void {
    const id = this.ids[a]
    this.ids[a] = this.ids[b]
    this.ids[b] = id
    const key = this.keys[a]
    this.keys[a] = this.keys[b]
    this.keys[b] = key
  }
}

interface Workspace {
  gScore: Float32Array
  /** 0 = sin visitar, 1 = en la cola, 2 = cerrada (ya expandida). */
  state: Uint8Array
  cameFrom: Int32Array
  heap: MinHeap
}

function createWorkspace(cells: number): Workspace {
  return {
    gScore: new Float32Array(cells),
    state: new Uint8Array(cells),
    cameFrom: new Int32Array(cells),
    heap: new MinHeap(4096),
  }
}

interface SearchResult {
  cells: number[] | null
  truncated: boolean
  visited: number
}

/** Mueve el extremo a la celda transitable más cercana (anillos de radio creciente). */
function snapToPassable(meta: TerrainField['meta'], severity: Uint8Array, cell: number, maxSeverity: number): number {
  if (cell < 0 || severity[cell] <= maxSeverity) return cell
  const startCol = cell % meta.width
  const startRow = (cell / meta.width) | 0
  for (let radius = 1; radius <= SNAP_RADIUS; radius += 1) {
    let best = -1
    let bestSeverity = Infinity
    for (let dy = -radius; dy <= radius; dy += 1) {
      for (let dx = -radius; dx <= radius; dx += 1) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== radius) continue
        const col = startCol + dx
        const row = startRow + dy
        if (col < 0 || row < 0 || col >= meta.width || row >= meta.height) continue
        const candidate = row * meta.width + col
        if (severity[candidate] <= maxSeverity && severity[candidate] < bestSeverity) {
          best = candidate
          bestSeverity = severity[candidate]
        }
      }
    }
    if (best >= 0) return best
  }
  return -1
}

function search(
  field: TerrainField,
  start: number,
  goal: number,
  options: PlanOptions,
  workspace: Workspace,
  maxExpansions: number,
): SearchResult {
  const { meta, severity, elevation } = field
  const { width, height, resolution } = meta
  const goalCol = goal % width
  const goalRow = (goal / width) | 0
  const { gScore, state, cameFrom, heap } = workspace
  state.fill(0)
  heap.clear()

  const stepBase = [
    resolution.x, resolution.x, resolution.y, resolution.y,
    Math.hypot(resolution.x, resolution.y), Math.hypot(resolution.x, resolution.y),
    Math.hypot(resolution.x, resolution.y), Math.hypot(resolution.x, resolution.y),
  ]

  const climb = Math.max(0, options.climbPenalty ?? 0)
  const descent = Math.max(0, Math.min(1, options.descentFactor ?? DEFAULT_DESCENT_FACTOR))
  // Metros de recorrido equivalente por punto de índice de altura (0 si no hay altura).
  const climbPerIndex = elevation && climb > 0 ? climb * field.metresPerIndex : 0

  gScore[start] = 0
  state[start] = 1
  cameFrom[start] = -1
  heap.push(start, 0)
  let expanded = 0

  while (heap.size > 0) {
    const current = heap.pop()
    // Entradas obsoletas: el nodo ya se expandió con un costo mejor.
    if (state[current] === 2) continue
    state[current] = 2
    if (current === goal) {
      const cells: number[] = []
      for (let cell = goal; cell !== -1; cell = cameFrom[cell]) cells.push(cell)
      cells.reverse()
      return { cells, truncated: false, visited: expanded }
    }
    if (expanded >= maxExpansions) return { cells: null, truncated: true, visited: expanded }
    expanded += 1

    const col = current % width
    const row = (current / width) | 0
    const currentSeverity = severity[current]
    const currentHeight = elevation ? elevation[current] : 0

    for (let direction = 0; direction < 8; direction += 1) {
      const dx = NEIGHBOUR_DX[direction]
      const dy = NEIGHBOUR_DY[direction]
      const nextCol = col + dx
      const nextRow = row + dy
      if (nextCol < 0 || nextRow < 0 || nextCol >= width || nextRow >= height) continue
      const next = nextRow * width + nextCol
      if (state[next] === 2) continue
      if (severity[next] > options.maxSeverity) continue
      // Sin cortar esquinas en diagonal: ambos flancos deben ser transitables.
      if (direction >= DIAGONAL_FROM) {
        const horizontal = row * width + nextCol
        const vertical = nextRow * width + col
        if (severity[horizontal] > options.maxSeverity || severity[vertical] > options.maxSeverity) continue
      }
      const multiplier = (slopeCost(currentSeverity, options.slopePenalty) + slopeCost(severity[next], options.slopePenalty)) / 2
      let step = stepBase[direction] * multiplier
      if (climbPerIndex > 0) {
        // El desnivel se compara con la distancia real del paso: subir 60 m en una celda
        // cuesta `climb` veces ese desnivel, bajar solo su fracción.
        const delta = (elevation ? elevation[next] : 0) - currentHeight
        step += climbCost(delta * field.metresPerIndex, climb, descent)
      }
      const tentative = gScore[current] + step
      if (state[next] === 1 && tentative >= gScore[next]) continue
      state[next] = 1
      gScore[next] = tentative
      cameFrom[next] = current
      // La heurística es la distancia geométrica: el costo por metro nunca baja de 1.
      const heuristic = Math.hypot((nextCol - goalCol) * resolution.x, (nextRow - goalRow) * resolution.y)
      heap.push(next, tentative + heuristic)
    }
  }
  return { cells: null, truncated: false, visited: expanded }
}

/** Douglas-Peucker: quita vértices que no aportan forma al trazado. */
export function simplifyPath(path: RoutePoint[], tolerance: number): RoutePoint[] {
  if (path.length < 3 || tolerance <= 0) return path
  const keep = new Uint8Array(path.length)
  keep[0] = 1
  keep[path.length - 1] = 1
  const stack: [number, number][] = [[0, path.length - 1]]
  while (stack.length > 0) {
    const [first, last] = stack.pop() as [number, number]
    const [ax, ay] = path[first]
    const [bx, by] = path[last]
    const segment = Math.hypot(bx - ax, by - ay)
    let farthest = -1
    let farthestDistance = tolerance
    for (let index = first + 1; index < last; index += 1) {
      const [px, py] = path[index]
      const distance = segment === 0
        ? Math.hypot(px - ax, py - ay)
        : Math.abs((by - ay) * px - (bx - ax) * py + bx * ay - by * ax) / segment
      if (distance > farthestDistance) {
        farthestDistance = distance
        farthest = index
      }
    }
    if (farthest > 0) {
      keep[farthest] = 1
      stack.push([first, farthest], [farthest, last])
    }
  }
  return path.filter((_, index) => keep[index] === 1)
}

/** Chaikin: redondea las esquinas del trazado sin mover sus extremos. */
export function smoothPath(path: RoutePoint[], iterations = 1): RoutePoint[] {
  let current = path
  for (let pass = 0; pass < iterations; pass += 1) {
    if (current.length < 3) return current
    const next: RoutePoint[] = [current[0]]
    for (let index = 1; index < current.length; index += 1) {
      const [ax, ay] = current[index - 1]
      const [bx, by] = current[index]
      next.push([ax * 0.75 + bx * 0.25, ay * 0.75 + by * 0.25])
      if (index < current.length - 1) next.push([ax * 0.25 + bx * 0.75, ay * 0.25 + by * 0.75])
    }
    next.push(current[current.length - 1])
    current = next
  }
  return current
}

export interface PathMeasurement extends ElevationStats {
  distance: number
  cost: number
  maxSeverity: number
}

/** Recorre un trazado celda a celda y acumula longitud, costo, pendiente y desnivel. */
function walkPath(field: TerrainField, path: RoutePoint[], options: PlanOptions): PathMeasurement {
  const { meta, severity, elevation } = field
  const sample = Math.min(meta.resolution.x, meta.resolution.y) / 2
  const climb = Math.max(0, options.climbPenalty ?? 0)
  const descent = Math.max(0, Math.min(1, options.descentFactor ?? DEFAULT_DESCENT_FACTOR))
  let distance = 0
  let cost = 0
  let maxSeverity = 0
  let ascent = 0
  let descentMetres = 0
  let maxGrade = 0
  let previousHeight: number | null = null
  for (let index = 1; index < path.length; index += 1) {
    const [ax, ay] = path[index - 1]
    const [bx, by] = path[index]
    const length = Math.hypot(bx - ax, by - ay)
    if (length === 0) continue
    const steps = Math.max(1, Math.ceil(length / sample))
    const fraction = length / steps
    for (let step = 0; step < steps; step += 1) {
      const t = (step + 0.5) / steps
      const cell = cellFromCoordinate(meta, [ax + (bx - ax) * t, ay + (by - ay) * t])
      const value = cell < 0 ? 0 : severity[cell]
      if (value > maxSeverity) maxSeverity = value
      distance += fraction
      cost += fraction * slopeCost(value, options.slopePenalty)
      // El desnivel se mide siempre; el planificador solo lo cobra si se le pide.
      if (elevation && cell >= 0) {
        const height = elevation[cell] * field.metresPerIndex
        if (previousHeight !== null) {
          const delta = height - previousHeight
          if (delta > 0) ascent += delta
          else descentMetres -= delta
          const grade = Math.abs(delta) / fraction * 100
          if (grade > maxGrade) maxGrade = grade
          if (climb > 0) cost += climbCost(delta, climb, descent)
        }
        previousHeight = height
      }
    }
  }
  return { distance, cost, maxSeverity, ascent, descent: descentMetres, maxGrade, straightAscent: 0 }
}

/** Longitud, costo, pendiente y desnivel de un trazado, muestreado sobre la malla. */
export function measurePath(field: TerrainField, path: RoutePoint[], options: PlanOptions): PathMeasurement {
  return walkPath(field, path, options)
}

/** Desnivel acumulado al recorrer en línea recta entre dos puntos. */
export function straightAscent(field: TerrainField, from: RoutePoint, to: RoutePoint): number {
  if (!field.elevation) return 0
  const { meta, elevation } = field
  const length = Math.hypot(to[0] - from[0], to[1] - from[1])
  const sample = Math.min(meta.resolution.x, meta.resolution.y) / 2
  const steps = Math.max(1, Math.ceil(length / sample))
  let ascent = 0
  let previous: number | null = null
  for (let step = 0; step <= steps; step += 1) {
    const t = step / steps
    const cell = cellFromCoordinate(meta, [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t])
    if (cell < 0) continue
    const height = elevation[cell] * field.metresPerIndex
    if (previous !== null && height > previous) ascent += height - previous
    previous = height
  }
  return ascent
}

function failLeg(index: number, from: RoutePoint, to: RoutePoint, reason: string): LegPlan {
  return {
    index, ok: false, from, to, path: [from, to], distance: 0,
    straight: Math.hypot(to[0] - from[0], to[1] - from[1]),
    cost: 0, maxSeverity: 0, snapped: 0, truncated: false,
    ascent: 0, descent: 0, maxGrade: 0, straightAscent: 0,
    reason,
  }
}

export function planRoute(
  field: TerrainField,
  points: RoutePoint[],
  options: PlanOptions,
  maxExpansions = DEFAULT_MAX_EXPANSIONS,
): RoutePlan {
  const started = typeof performance === 'undefined' ? Date.now() : performance.now()
  const { meta, severity } = field
  if (severity.length !== meta.width * meta.height) throw new Error('La malla no coincide con su ficha.')
  if (field.elevation && field.elevation.length !== severity.length) throw new Error('La malla de altura no coincide con la de pendientes.')
  const settings: PlanOptions = {
    maxSeverity: Math.min(255, Math.max(0, Math.round(options.maxSeverity))),
    slopePenalty: Math.max(0, options.slopePenalty),
    climbPenalty: Math.max(0, options.climbPenalty ?? 0),
    descentFactor: Math.max(0, Math.min(1, options.descentFactor ?? DEFAULT_DESCENT_FACTOR)),
  }
  const workspace = createWorkspace(severity.length)
  const tolerance = Math.min(meta.resolution.x, meta.resolution.y) * 1.1

  const legs: LegPlan[] = []
  let visited = 0

  for (let index = 0; index + 1 < points.length; index += 1) {
    const from = points[index]
    const to = points[index + 1]
    const startCell = cellFromCoordinate(meta, from)
    const goalCell = cellFromCoordinate(meta, to)
    if (startCell < 0 || goalCell < 0) {
      legs.push(failLeg(index, from, to, 'El punto queda fuera de la malla del MDE.'))
      continue
    }
    // Los extremos sobre terreno demasiado inclinado se acercan al borde transitable.
    const snappedStart = snapToPassable(meta, severity, startCell, settings.maxSeverity)
    const snappedGoal = snapToPassable(meta, severity, goalCell, settings.maxSeverity)
    if (snappedStart < 0 || snappedGoal < 0) {
      legs.push(failLeg(index, from, to, 'No hay terreno transitable cerca de uno de los puntos.'))
      continue
    }
    const startCenter = coordinateFromCell(meta, snappedStart)
    const goalCenter = coordinateFromCell(meta, snappedGoal)
    const snapped = Math.hypot(startCenter[0] - from[0], startCenter[1] - from[1]) +
      Math.hypot(goalCenter[0] - to[0], goalCenter[1] - to[1])

    const result = snappedStart === snappedGoal
      ? { cells: [snappedStart, snappedGoal], truncated: false, visited: 0 }
      : search(field, snappedStart, snappedGoal, settings, workspace, maxExpansions)
    visited += result.visited
    if (!result.cells || result.cells.length < 2) {
      legs.push({
        ...failLeg(index, from, to, result.truncated
          ? 'La búsqueda superó el límite de celdas; acorta el tramo o sube la tolerancia.'
          : 'No hay paso entre ambos puntos con esta tolerancia de pendiente.'),
        snapped,
        truncated: result.truncated,
      })
      continue
    }

    const centers = result.cells.map(cell => coordinateFromCell(meta, cell))
    if (snapped < 1) {
      centers[0] = from
      centers[centers.length - 1] = to
    } else {
      centers.unshift(from)
      centers.push(to)
    }
    const path = smoothPath(simplifyPath(centers, tolerance))
    const measured = walkPath(field, path, settings)
    const maxSeverity = result.cells.reduce((max, cell) => Math.max(max, severity[cell]), 0)

    legs.push({
      index,
      ok: true,
      from,
      to,
      path,
      distance: measured.distance,
      straight: Math.hypot(to[0] - from[0], to[1] - from[1]),
      cost: measured.cost,
      maxSeverity,
      snapped,
      truncated: false,
      ascent: measured.ascent,
      descent: measured.descent,
      maxGrade: measured.maxGrade,
      straightAscent: straightAscent(field, from, to),
    })
  }

  const total = (pick: (leg: LegPlan) => number) => legs.reduce((sum, leg) => sum + pick(leg), 0)
  const distance = total(leg => leg.distance)
  const cost = total(leg => leg.cost)
  const straight = total(leg => leg.straight)
  const failedLegs = legs.filter(leg => !leg.ok).map(leg => leg.index)
  const ascent = total(leg => leg.ascent)
  const descent = total(leg => leg.descent)

  // Referencia "sin altura": el mismo encargo resuelto ignorando el desnivel.
  // Comparar contra la línea recta engaña cuando la recta cruza una pared que no
  // es transitable; comparar contra este trazado sí aísla el efecto del ascenso.
  const baseline = (settings.climbPenalty ?? 0) > 0 && field.elevation
    ? planRoute(field, points, { ...settings, climbPenalty: 0 }, maxExpansions)
    : null
  const baselineAscent = baseline ? baseline.ascent : ascent
  const baselineDistance = baseline ? baseline.distance : distance
  const baselineDescent = baseline ? baseline.descent : descent

  return {
    ok: legs.length > 0 && failedLegs.length === 0,
    legs,
    distance,
    straight,
    cost,
    effort: distance > 0 ? cost / distance : 1,
    maxSeverity: legs.reduce((max, leg) => Math.max(max, leg.maxSeverity), 0),
    truncated: legs.some(leg => leg.truncated),
    failedLegs,
    visited,
    elapsed: (typeof performance === 'undefined' ? Date.now() : performance.now()) - started,
    ascent,
    descent,
    maxGrade: legs.reduce((max, leg) => Math.max(max, leg.maxGrade), 0),
    straightAscent: total(leg => leg.straightAscent),
    baselineAscent,
    baselineDistance,
    baselineDescent,
    savedAscent: Math.max(0, baselineAscent - ascent),
    detourForClimb: distance - baselineDistance,
  }
}

/** Promedio de severidad sobre una línea recta, para contrastar con la ruta. */
export function straightSeverity(meta: TerrainField['meta'], severity: Uint8Array, from: RoutePoint, to: RoutePoint): number {
  const steps = 160
  let total = 0
  for (let step = 0; step <= steps; step += 1) {
    const t = step / steps
    const cell = cellFromCoordinate(meta, [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t])
    total += cell < 0 ? 0 : severity[cell]
  }
  return total / (steps + 1)
}
