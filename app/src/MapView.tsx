import { useEffect, useRef } from 'react'
import Map from 'ol/Map'
import View from 'ol/View'
import Feature from 'ol/Feature'
import type { FeatureLike } from 'ol/Feature'
import ImageLayer from 'ol/layer/Image'
import ImageStatic from 'ol/source/ImageStatic'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Point from 'ol/geom/Point'
import LineString from 'ol/geom/LineString'
import Style from 'ol/style/Style'
import Stroke from 'ol/style/Stroke'
import Fill from 'ol/style/Fill'
import CircleStyle from 'ol/style/Circle'
import Text from 'ol/style/Text'
import { boundingExtent, createEmpty, extend, getCenter, getHeight, getWidth } from 'ol/extent'
import type { Extent } from 'ol/extent'
import type { Coordinate } from 'ol/coordinate'
import { defaults as defaultControls } from 'ol/control'
import proj4 from 'proj4'
import { register } from 'ol/proj/proj4'
import type { MapImage } from './layers'
import type { RoutePlan, RoutePoint } from './routing/planner'
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
  route: RoutePlan | null
  points: RoutePoint[]
  adding: boolean
  onMapClick: (point: RoutePoint) => void
}

const ROUTE_COLOR = '#a45030'
const HALO_COLOR = '#fcfaf6'
const FAILED_COLOR = '#9b3525'
const INK = '#303d38'

const routeHalo = new Style({ stroke: new Stroke({ color: HALO_COLOR, width: 9, lineCap: 'round', lineJoin: 'round' }) })
const routeLine = new Style({ stroke: new Stroke({ color: ROUTE_COLOR, width: 3.5, lineCap: 'round', lineJoin: 'round' }) })
const failedLine = new Style({ stroke: new Stroke({ color: FAILED_COLOR, width: 2, lineDash: [4, 8], lineCap: 'round' }) })
const waypointStyles: Record<string, Style> = {}

function waypointStyle(label: string): Style {
  const cached = waypointStyles[label]
  if (cached) return cached
  const style = new Style({
    image: new CircleStyle({ radius: 9, fill: new Fill({ color: HALO_COLOR }), stroke: new Stroke({ color: INK, width: 2 }) }),
    text: new Text({
      font: '700 11px "DM Sans", system-ui, sans-serif', fill: new Fill({ color: INK }),
      text: label, textAlign: 'center', textBaseline: 'middle', offsetY: 0.5,
    }),
  })
  waypointStyles[label] = style
  return style
}

function styleFor(feature: FeatureLike): Style | Style[] {
  if (feature.get('kind') === 'route') return [routeHalo, routeLine]
  if (feature.get('kind') === 'failed') return failedLine
  return waypointStyle(String(feature.get('label')))
}

/* El mapa es el fondo de toda la página: encuadramos la imagen en modo «cubrir»
   para que no queden franjas vacías alrededor del terreno. */
function fitCover(instance: Map, extent: Extent, duration = 0) {
  const size = instance.getSize()
  const view = instance.getView()
  if (!size || !size[0] || !size[1]) {
    view.fit(extent, { maxZoom: 20 })
    return
  }
  /* 6 % de zoom extra: el terreno llena la pantalla sin dejar franjas vacías. */
  const resolution = Math.min(
    getWidth(extent) / size[0],
    getHeight(extent) / size[1],
  ) * 0.94
  view.animate({ center: getCenter(extent) as Coordinate, resolution, duration })
}

function buildFeatures(route: RoutePlan | null, points: RoutePoint[]): Feature[] {
  const features: Feature[] = []
  route?.legs.forEach(leg => {
    if (leg.path.length > 1) {
      features.push(new Feature({
        geometry: new LineString(leg.path),
        kind: leg.ok ? 'route' : 'failed',
      }))
    }
  })
  points.forEach((point, index) => {
    features.push(new Feature({ geometry: new Point(point), kind: 'waypoint', label: index + 1 }))
  })
  return features
}

export function MapView({ layers, settings, onStatus, route, points, adding, onMapClick }: Props) {
  const target = useRef<HTMLDivElement>(null)
  const map = useRef<Map | null>(null)
  const images = useRef<Record<string, ImageLayer<ImageStatic>>>({})
  const vectorSource = useRef<VectorSource | null>(null)
  const clickHandler = useRef(onMapClick)
  const addingRef = useRef(adding)
  clickHandler.current = onMapClick
  addingRef.current = adding

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

    const source = new VectorSource()
    vectorSource.current = source
    const routeLayer = new VectorLayer({ source, style: styleFor, zIndex: 20 })

    const instance = new Map({
      target: target.current!,
      controls: defaultControls({ zoom: false, rotate: false, attribution: false }),
      layers: [...imageLayers, routeLayer],
      view: new View({ projection: 'MARS:JEZERO', center: [0, 0], zoom: 2, maxZoom: 24 }),
    })
    map.current = instance
    instance.on('click', event => {
      if (!addingRef.current) return
      clickHandler.current([event.coordinate[0], event.coordinate[1]])
    })
    if (layers.length) fitCover(instance, extent)
    return () => {
      instance.setTarget(undefined)
      instance.dispose()
      images.current = {}
      vectorSource.current = null
      map.current = null
    }
  }, [layers, onStatus])

  useEffect(() => {
    Object.entries(settings).forEach(([id, setting]) => {
      images.current[id]?.setVisible(setting.visible)
      images.current[id]?.setOpacity(setting.opacity / 100)
    })
  }, [settings, layers])

  useEffect(() => {
    const source = vectorSource.current
    if (!source) return
    source.clear()
    source.addFeatures(buildFeatures(route, points))
  }, [route, points, layers])

  /* Al cambiar los puntos (no al recalcular el trazado) encuadramos el tramo:
     a escala de Jezero una travesía de 3 km ocupa unos pocos píxeles. */
  const framed = useRef('')
  useEffect(() => {
    const instance = map.current
    if (!instance || points.length < 2) return
    const key = points.map(point => point.join(',')).join(';')
    if (key === framed.current) return
    framed.current = key
    const coords: Coordinate[] = []
    route?.legs.forEach(leg => leg.path.forEach(point => coords.push(point)))
    points.forEach(point => coords.push(point))
    if (coords.length < 2) return
    const extent = boundingExtent(coords)
    instance.getView().fit(extent, {
      padding: [90, 90, 120, 400],
      maxZoom: 18,
      duration: 320,
    })
  }, [route, points])

  function reset() {
      if (!layers.length) return
      const extent = createEmpty()
      layers.forEach(layer => extend(extent, layer.extent))
      const instance = map.current
      if (instance) fitCover(instance, extent, 200)
    }

  const summary = route && route.ok ? `${(route.distance / 1000).toFixed(1).replace('.', ',')} km · ${route.legs.length} ${route.legs.length === 1 ? 'tramo' : 'tramos'}` : null

  return (
    <section className={adding ? 'map is-adding' : 'map'} aria-label="Mapa de Jezero">
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
      {adding && <div className="map-hint" role="status">Haz clic en el mapa para añadir el siguiente punto</div>}
      {!layers.length && <div className="empty-map">
        <div className="orbit" aria-hidden="true">◎</div>
        <span className="eyebrow">EL PUNTO DE PARTIDA</span>
        <h2>Mapa pendiente de cargar</h2>
        <p>Aquí aparecerán las imágenes de Jezero y sus capas, cuando incorporemos los recursos de NASA.</p>
        <span className="tag">Sin datos de demostración</span>
      </div>}
      {summary && <div className="map-caption route-caption"><span className="dot" /> {summary}</div>}
      <div className="map-caption">2D · Imágenes y capas georreferenciadas</div>
    </section>
  )
}