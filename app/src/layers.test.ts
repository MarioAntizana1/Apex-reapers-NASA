import { describe, expect, it } from 'vitest'
import { parseLayers } from './layers'

const image = {
  id: 'test-image', name: 'Imagen de prueba', url: 'maps/test.png',
  extent: [-100, -100, 100, 100], source: 'https://science.nasa.gov/',
  description: 'Recurso sintético de prueba, no científico.',
  mission: 'Prueba', instrument: 'Prueba', resolution: 'No aplica',
  date: 'No aplica', license: 'Prueba', limitations: 'No usar para navegación',
}

describe('contrato de imágenes', () => {
  it('acepta un manifiesto vacío sin inventar capas', () => {
    expect(parseLayers({ layers: [] })).toEqual([])
  })

  it('conserva extensión, procedencia y archivo de una imagen válida', () => {
    expect(parseLayers({ layers: [image] })).toEqual([image])
  })

  it.each([
    null, {}, { layers: {} }, { layers: [null] },
    { layers: [image, image] },
    { layers: [{ ...image, extent: [100, -100, -100, 100] }] },
    { layers: [{ ...image, extent: [0, 0, 0, 10] }] },
    { layers: [{ ...image, extent: [0, 0, Infinity, 10] }] },
    { layers: [{ ...image, url: 'javascript:alert(1)' }] },
    { layers: [{ ...image, url: '//outside.example/test.png' }] },
    { layers: [{ ...image, source: 'javascript:alert(1)' }] },
    { layers: [{ ...image, mission: '' }] },
  ])('rechaza configuración incompleta o insegura: %j', (manifest) => {
    expect(() => parseLayers(manifest)).toThrow()
  })
})
