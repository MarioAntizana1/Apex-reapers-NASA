import { useEffect, useRef } from 'react'
import Map from 'ol/Map'
import View from 'ol/View'
import ImageLayer from 'ol/layer/Image'
import ImageStatic from 'ol/source/ImageStatic'
import { createEmpty, extend } from 'ol/extent'
import { defaults as defaultControls } from 'ol/control'
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'
import type { MapImage } from './layers'
import 'ol/ol.css'

// SUPUESTO cartográfico inicial: esfera y proyección local, no cobertura validada.
proj4.defs('MARS:JEZERO',
  '+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs')
register(proj4)

export type LayerState = { visible: boolean; opacity: number }
export type ImageStatus = 'loading' | 'loaded' | 'error'

interface Props {
  layers: MapImage[]
  settings: Record<string, LayerState>
  onStatus: (id: string, status: ImageStatus) => void
}

export function MapView({ layers, settings, onStatus }: Props) {
  const target = useRef<HTMLDivElement>(null)
  const map = useRef<Map | null>(null)
  const images = useRef<Record<string, ImageLayer<ImageStatic>>>({})

  useEffect(() => {
    const extent = createEmpty()
    const imageLayers = layers.map(layer => {
      extend(extent, layer.extent)
      const source = new ImageStatic({
        url: `${import.meta.env.BASE_URL}${layer.url}`,
        projection: 'MARS:JEZERO',
        imageExtent: layer.extent,
      })
      source.on('imageloadstart', () => onStatus(layer.id, 'loading'))
      source.on('imageloadend', () => onStatus(layer.id, 'loaded'))
      source.on('imageloaderror', () => onStatus(layer.id, 'error'))
      const image = new ImageLayer({ source })
      images.current[layer.id] = image
      return image
    })
    const instance = new Map({
      target: target.current!,
      controls: defaultControls({ zoom: false, rotate: false, attribution: false }),
      layers: imageLayers,
      view: new View({ projection: 'MARS:JEZERO', center: [0, 0], zoom: 2, maxZoom: 24 }),
    })
    map.current = instance
    if (layers.length) instance.getView().fit(extent, { padding: [40, 40, 40, 40], maxZoom: 20 })
    return () => {
      instance.setTarget(undefined)
      instance.dispose()
      images.current = {}
      map.current = null
    }
  }, [layers, onStatus])

  useEffect(() => {
    Object.entries(settings).forEach(([id, setting]) => {
      images.current[id]?.setVisible(setting.visible)
      images.current[id]?.setOpacity(setting.opacity / 100)
    })
  }, [settings, layers])

  function reset() {
    if (!layers.length) return
    const extent = createEmpty()
    layers.forEach(layer => extend(extent, layer.extent))
    map.current?.getView().fit(extent, { padding: [40, 40, 40, 40], maxZoom: 20, duration: 200 })
  }

  return (
    <section className="map" aria-label="Mapa de Jezero">
      <div ref={target} className="map-canvas" tabIndex={0}
        aria-label="Mapa interactivo: arrastra para desplazarte; usa más y menos para el zoom" />
      <div className="map-label"><span className="dot" /> JEZERO / VISTA CARTOGRÁFICA</div>
      <div className="map-controls">
        <button aria-label="Acercar" disabled={!layers.length} onClick={() => {
          const view = map.current?.getView()
          view?.animate({ zoom: (view.getZoom() ?? 2) + 1, duration: 150 })
        }}>+</button>
        <button aria-label="Alejar" disabled={!layers.length} onClick={() => {
          const view = map.current?.getView()
          view?.animate({ zoom: (view.getZoom() ?? 2) - 1, duration: 150 })
        }}>−</button>
        <button aria-label="Restablecer vista" disabled={!layers.length} onClick={reset}>↺</button>
      </div>
      {!layers.length && <div className="empty-map">
        <div className="orbit" aria-hidden="true">◎</div>
        <span className="eyebrow">EL PUNTO DE PARTIDA</span>
        <h2>Mapa pendiente de cargar</h2>
        <p>Aquí aparecerán las imágenes de Jezero y sus capas, cuando incorporemos los recursos de NASA.</p>
        <span className="tag">Sin datos de demostración</span>
      </div>}
      <div className="map-caption">2D · Imágenes y capas georreferenciadas</div>
    </section>
  )
}
