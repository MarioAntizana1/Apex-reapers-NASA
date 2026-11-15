/**
 * Mallas de terreno del MDE CTX.
 *
 * `terrain/terrain.json` declara dos rejillas sobre la MISMA ventana de Jezero:
 *
 * - `slope`: índice RELATIVO 0-255 por celda (0 = llano, 255 = el tono más alto de la
 *   rampa de pendientes). No son grados: la capa de origen no trae leyenda numérica.
 * - `elevation`: altura relativa 0-255 con su equivalencia aproximada en metros
 *   (`metresPerIndex`). Es la que permite decidir entre subir un desnivel o rodearlo.
 *
 * Ambas rejillas comparten extensión, tamaño y origen, así que la celda `i` de una y
 * de otra es el mismo punto del mapa.
 */

export type Extent = [number, number, number, number]

/** Datos comunes a cada rejilla declarada en la ficha. */
export interface RasterMeta {
  grid: string
  sourceLayer: string
  sourceImage: string
  units: string
  notes?: string[]
}

export interface ElevationMeta extends RasterMeta {
  /** Metros que representa cada punto del índice 0-255. */
  metresPerIndex: number
  /** Desnivel total asumido para la ventana; solo informativo. */
  reliefMetres?: number
  smoothCells?: number
}

export interface TerrainMeta {
  id: string
  name: string
  extent: Extent
  width: number
  height: number
  resolution: { x: number; y: number }
  origin: string
  notes: string[]
  generated: string
  slope: RasterMeta
  elevation: ElevationMeta | null
}

/** Rejillas ya decodificadas, listas para el planificador. */
export interface TerrainField {
  meta: TerrainMeta
  /** Índice de pendiente por celda, fila por fila desde el borde superior. */
  severity: Uint8Array
  /** Altura relativa por celda con el mismo orden; nula si la ficha no la declara. */
  elevation: Uint8Array | null
  /** Metros por punto del índice de altura (0 si no hay altura). */
  metresPerIndex: number
}

/** Desnivel por omisión cuando la ficha no lo declara. */
const DEFAULT_RELIEF_METRES = 2000

function isPng(grid: unknown): grid is string {
  return typeof grid === 'string' && grid.endsWith('.png')
}

function readRaster(value: unknown, label: string): RasterMeta {
  if (!value || typeof value !== 'object') throw new Error(`La ficha no declara la malla de ${label}.`)
  const raster = value as Record<string, unknown>
  if (!isPng(raster.grid)) throw new Error(`La malla de ${label} no declara su archivo .png.`)
  return {
    grid: raster.grid,
    sourceLayer: typeof raster.sourceLayer === 'string' ? raster.sourceLayer : '',
    sourceImage: typeof raster.sourceImage === 'string' ? raster.sourceImage : '',
    units: typeof raster.units === 'string' ? raster.units : '',
    notes: Array.isArray(raster.notes) ? raster.notes.filter((note): note is string => typeof note === 'string') : [],
  }
}

function readElevation(value: unknown): ElevationMeta {
  const raster = readRaster(value, 'altura')
  const source = value as Record<string, unknown>
  const relief = Number(source.reliefMetres)
  const declared = Number(source.metresPerIndex)
  const metresPerIndex = Number.isFinite(declared) && declared > 0
    ? declared
    : Number.isFinite(relief) && relief > 0 ? relief / 255 : DEFAULT_RELIEF_METRES / 255
  return {
    ...raster,
    metresPerIndex,
    reliefMetres: Number.isFinite(relief) && relief > 0 ? relief : 255 * metresPerIndex,
    smoothCells: Number(source.smoothCells) || undefined,
  }
}

export function parseTerrainMeta(value: unknown): TerrainMeta {
  if (!value || typeof value !== 'object') throw new Error('La ficha de la malla de terreno no existe.')
  const raw = value as Record<string, unknown>
  const extent = raw.extent
  if (!Array.isArray(extent) || extent.length !== 4 || !extent.every(n => typeof n === 'number' && Number.isFinite(n)) ||
    extent[0] >= extent[2] || extent[1] >= extent[3]) {
    throw new Error('La extensión de la malla no es [xmin, ymin, xmax, ymax].')
  }
  const width = raw.width
  const height = raw.height
  if (!Number.isInteger(width) || !Number.isInteger(height) || (width as number) < 2 || (height as number) < 2) {
    throw new Error('La malla declara dimensiones inválidas.')
  }
  const resolution = raw.resolution as { x?: unknown; y?: unknown } | undefined
  if (!resolution || !(Number(resolution.x) > 0) || !(Number(resolution.y) > 0)) {
    throw new Error('La malla declara una resolución inválida.')
  }
  // La ficha nueva anida cada rejilla; la antigua tenía la pendiente en la raíz.
  const slope = readRaster(raw.slope ?? raw, 'pendiente')

  return {
    id: String(raw.id ?? 'terrain'),
    name: String(raw.name ?? 'Malla de terreno'),
    extent: extent as Extent,
    width: width as number,
    height: height as number,
    resolution: { x: Number(resolution.x), y: Number(resolution.y) },
    origin: String(raw.origin ?? 'top-left'),
    notes: Array.isArray(raw.notes) ? raw.notes.filter((note): note is string => typeof note === 'string') : [],
    generated: String(raw.generated ?? ''),
    slope,
    elevation: raw.elevation == null ? null : readElevation(raw.elevation),
  }
}

/** Índice de la celda que contiene la coordenada, o -1 si cae fuera del mapa. */
export function cellFromCoordinate(meta: TerrainMeta, [x, y]: [number, number]): number {
  const [xmin, , , ymax] = meta.extent
  const col = Math.floor((x - xmin) / meta.resolution.x)
  const row = Math.floor((ymax - y) / meta.resolution.y)
  if (col < 0 || row < 0 || col >= meta.width || row >= meta.height) return -1
  return row * meta.width + col
}

export function coordinateFromCell(meta: TerrainMeta, cell: number): [number, number] {
  const col = cell % meta.width
  const row = (cell / meta.width) | 0
  const [xmin, , , ymax] = meta.extent
  return [xmin + (col + 0.5) * meta.resolution.x, ymax - (row + 0.5) * meta.resolution.y]
}

export function cellSeverity(meta: TerrainMeta, severity: Uint8Array, point: [number, number]): number | null {
  const cell = cellFromCoordinate(meta, point)
  return cell < 0 ? null : severity[cell]
}

/** Metros sobre la base de la ventana en ese punto, o nulo si queda fuera. */
export function cellElevation(field: TerrainField, point: [number, number]): number | null {
  if (!field.elevation) return null
  const cell = cellFromCoordinate(field.meta, point)
  return cell < 0 ? null : field.elevation[cell] * field.metresPerIndex
}

/** Fichas aceptadas, en orden. */
const META_CANDIDATES = ['terrain/terrain.json', 'terrain/slope_index.json']

async function decodeGrid(baseUrl: string, grid: string, meta: TerrainMeta, label: string, signal?: AbortSignal): Promise<Uint8Array> {
  const response = await fetch(`${baseUrl}${grid}`, { signal })
  if (!response.ok) throw new Error(`No se pudo leer la malla de ${label} (HTTP ${response.status}).`)
  const bitmap = await createImageBitmap(await response.blob())
  const canvas = document.createElement('canvas')
  canvas.width = meta.width
  canvas.height = meta.height
  const context = canvas.getContext('2d', { willReadFrequently: true })
  if (!context) throw new Error('El navegador no permitió decodificar la malla.')
  context.drawImage(bitmap, 0, 0, meta.width, meta.height)
  bitmap.close()
  const pixels = context.getImageData(0, 0, meta.width, meta.height).data
  const values = new Uint8Array(meta.width * meta.height)
  for (let index = 0; index < values.length; index += 1) values[index] = pixels[index * 4]
  return values
}

/** Descarga la ficha y las rejillas declaradas y las convierte en arrays de bytes. */
export async function loadTerrainField(baseUrl: string, signal?: AbortSignal): Promise<TerrainField> {
  let metaResponse: Response | null = null
  let status = 0
  for (const candidate of META_CANDIDATES) {
    const response = await fetch(`${baseUrl}${candidate}`, { signal })
    status = response.status
    if (response.ok) {
      metaResponse = response
      break
    }
  }
  if (!metaResponse) throw new Error(`No se pudo leer la ficha de la malla (HTTP ${status}).`)
  const meta = parseTerrainMeta(await metaResponse.json())

  const [severity, elevation] = await Promise.all([
    decodeGrid(baseUrl, meta.slope.grid, meta, 'pendientes', signal),
    meta.elevation ? decodeGrid(baseUrl, meta.elevation.grid, meta, 'altura', signal) : Promise.resolve(null),
  ])

  return {
    meta,
    severity,
    elevation,
    metresPerIndex: meta.elevation?.metresPerIndex ?? 0,
  }
}
