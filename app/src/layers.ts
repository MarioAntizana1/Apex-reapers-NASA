export interface MapImage {
  id: string
  name: string
  url: string
  extent: [number, number, number, number]
  source: string
  description: string
  mission: string
  instrument: string
  resolution: string
  date: string
  license: string
  limitations: string
}

export function parseLayers(value: unknown): MapImage[] {
  if (!value || typeof value !== 'object' || !('layers' in value) || !Array.isArray(value.layers)) {
    throw new Error('El manifiesto debe contener una lista de capas.')
  }
  const ids = new Set<string>()
  return value.layers.map((entry: unknown) => {
    if (!entry || typeof entry !== 'object') throw new Error('Ficha de capa inválida.')
    const layer = entry as MapImage
    const fields = ['id', 'name', 'url', 'source', 'description', 'mission', 'instrument',
      'resolution', 'date', 'license', 'limitations'] as const
    if (fields.some(field => typeof layer[field] !== 'string' || !layer[field].trim())) {
      throw new Error('Cada capa necesita una ficha completa.')
    }
    if (ids.has(layer.id)) throw new Error('Los identificadores de capa deben ser únicos.')
    ids.add(layer.id)
    // Solo archivos relativos al despliegue; las imágenes remotas se descargan y verifican primero.
    if (!/^[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_.-]+)*\.(png|jpe?g|webp|svg)$/i.test(layer.url) ||
      layer.url.split('/').includes('..')) throw new Error('Archivo de imagen local inválido.')
    try {
      if (new URL(layer.source).protocol !== 'https:') throw new Error()
    } catch {
      throw new Error('La fuente debe ser un enlace HTTPS.')
    }
    const extent = layer.extent
    if (!Array.isArray(extent) || extent.length !== 4 ||
      !extent.every(n => typeof n === 'number' && Number.isFinite(n)) ||
      extent[0] >= extent[2] || extent[1] >= extent[3]) {
      throw new Error('La extensión debe ser [xmin, ymin, xmax, ymax] en metros.')
    }
    return layer
  })
}
