import { useCallback, useEffect, useState } from 'react'
import { MapView, type ImageStatus, type LayerState } from './MapView'
import { parseLayers, type MapImage } from './layers'
import { useRoutePlanner } from './routing/useRoutePlanner'
import { DEFAULT_DESCENT_FACTOR, SEVERITY_PRESETS, type RoutePlan } from './routing/planner'
import './styles.css'

const km = (metres: number) => `${(metres / 1000).toFixed(1).replace('.', ',')} km`
const decimal = (value: number, digits = 2) => value.toFixed(digits).replace('.', ',')
const PRESET_LABELS: Record<keyof typeof SEVERITY_PRESETS, string> = {
  conservador: 'Conservador',
  estandar: 'Estándar',
  amplio: 'Amplio',
}

function RouteSummary({ plan, climb }: { plan: RoutePlan; climb: number }) {
  if (!plan.ok) {
    return <div className="route-failure" role="alert">
      <strong>Sin trazado con esta tolerancia.</strong>
      {plan.legs.filter(leg => !leg.ok).map(leg => <p key={leg.index}>Tramo {leg.index + 1}: {leg.reason}</p>)}
    </div>
  }
  const detour = plan.straight > 0 ? (plan.distance / plan.straight - 1) * 100 : 0
  const hasRelief = plan.ascent > 0 || plan.descent > 0
  // El ahorro se mide contra el trazado que ignora la altura: la línea recta puede
  // cruzar una pared intransitable y no ser un camino con el que compararse.
  const saves = plan.savedAscent
  const extra = plan.detourForClimb
  const metres = (value: number) => Math.round(value).toLocaleString('es-PE')
  const verdict = climb <= 0
    ? hasRelief
      ? 'Sin peso de ascenso el trazado no mira la altura: solo manda la distancia.'
      : 'El terreno no obliga a subir: manda la distancia.'
    : saves > 50
      ? extra > 1
        ? `Rodea el relieve: suma ${metres(extra)} m de ruta para ahorrar ${metres(saves)} m de subida.`
        : `Rodea el relieve sin pagar ruta: ahorra ${metres(saves)} m de subida.`
      : extra > 1
        ? `Sube directo: rodear costaría ${metres(extra)} m más de ruta sin ahorrar apenas subida.`
        : 'Sube directo: rodear no ahorra subida en este tramo.'
  return <>
    <dl className="route-stats">
      <div><dt>Ruta</dt><dd>{km(plan.distance)} <span>línea recta {km(plan.straight)}</span></dd></div>
      <div><dt>Desvío</dt><dd>{detour >= 0.05 ? `+${decimal(detour, 0)} %` : 'sin desvío'}</dd></div>
      {hasRelief && <div><dt>Ascenso</dt><dd>{metres(plan.ascent)} m
        <span>sin peso {metres(plan.baselineAscent)} m</span></dd></div>}
      {hasRelief && <div><dt>Descenso</dt><dd>{Math.round(plan.descent).toLocaleString('es-PE')} m
        <span>cuesta un {Math.round(DEFAULT_DESCENT_FACTOR * 100)} % del ascenso</span></dd></div>}
      <div><dt>Pendiente máx.</dt><dd>índice {plan.maxSeverity}/255</dd></div>
      {hasRelief && climb > 0 && <div><dt>Recta</dt><dd>{metres(plan.straightAscent)} m de subida
        <span>en {km(plan.straight)}, si fuera transitable</span></dd></div>}
      <div><dt>Esfuerzo</dt><dd>×{decimal(plan.effort)} sobre terreno liso</dd></div>
      <div><dt>Cálculo</dt><dd>{plan.visited.toLocaleString('es-PE')} celdas · {Math.round(plan.elapsed)} ms</dd></div>
    </dl>
    <p className="route-verdict" data-kind={saves > 50 ? 'rodea' : 'sube'}>{verdict}</p>
  </>
}

export default function App() {
  const [layers, setLayers] = useState<MapImage[]>([])
  const [settings, setSettings] = useState<Record<string, LayerState>>({})
  const [statuses, setStatuses] = useState<Record<string, ImageStatus>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  /* Modo «solo mapa»: por defecto no se muestra ningún panel sobre el terreno. */
  const [panelsOpen, setPanelsOpen] = useState(false)
  const route = useRoutePlanner()
  const onStatus = useCallback((id: string, status: ImageStatus) => {
    setStatuses(previous => ({ ...previous, [id]: status }))
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch(`${import.meta.env.BASE_URL}layers.json`, { signal: controller.signal })
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const parsed = parseLayers(await response.json())
        if (controller.signal.aborted) return
        setLayers(parsed)
        setSettings(Object.fromEntries(parsed.map((layer, index) => [layer.id, { visible: index === 0, opacity: 100 }])))
        setSelectedId(parsed[0]?.id ?? null)
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(`No se pudo cargar el catálogo de capas. ${reason instanceof Error ? reason.message : ''}`)
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => controller.abort()
  }, [])

  const selected = layers.find(layer => layer.id === selectedId)
  const statusLabels = { loading: 'Cargando imagen…', loaded: 'Capa cargada', error: 'No se pudo cargar la imagen' }
  const nextPointLabel = route.points.length === 0 ? 'Marcar inicio' : route.points.length === 1 ? 'Marcar destino' : 'Añadir parada'

  return (
    <div className={panelsOpen ? 'app panels-open' : 'app panels-closed'}>
      <header className="header">
        <a className="brand" href="./" aria-label="Apex-Mars, inicio">
          <span className="brand-icon" aria-hidden="true">a</span>
          <span>Apex<span className="brand-light">-Mars</span><small>Apex-Reapers</small></span>
        </a>
        <div className="location"><span className="dot" /><div>Jezero<small>MARTE · ÁREA DE EXPLORACIÓN</small></div></div>
        <div className="view-switch" role="group" aria-label="Vista del mapa">
          <button aria-pressed="true">2D</button>
          <button disabled aria-describedby="terrain-note">3D</button>
        </div>
      </header>

      <main className="workspace">
        <aside className="sidebar" id="workspace-panels" aria-label="Rutas, capas e información">
          <div className="panel-title"><span className="eyebrow">EXPLORA JEZERO</span><h1>Traza la ruta más corta.</h1>
            <p>El planificador lee el relieve y rodea lo que un rover no podría cruzar.</p></div>

          <section className="route-panel" aria-labelledby="route-title">
            <div className="section-heading"><h2 id="route-title">Planificador de ruta</h2>
              <span className="count">{route.points.length} pt</span></div>
            {route.state === 'error' ? <p className="error" role="alert">{route.error}</p> : route.state === 'cargando' ?
              <p className="route-status" role="status">Leyendo la malla de pendientes…</p> : <>
                <p className="route-lead">Cada celda de ~60 m cuesta más cuanto más inclinada está. Las pendientes
                  por encima de la tolerancia son intransitables.</p>
                <div className="route-actions">
                  <button type="button" className="primary" aria-pressed={route.adding}
                    onClick={() => route.setAdding(!route.adding)}>
                    {route.adding ? 'Clic en el mapa…' : nextPointLabel}</button>
                  <button type="button" onClick={route.undo} disabled={!route.points.length}>Deshacer</button>
                  <button type="button" onClick={route.clear} disabled={!route.points.length}>Borrar</button>
                </div>
                {route.points.length > 0 && <ol className="waypoint-list">
                  {route.points.map((point, index) => <li key={`${point[0]}-${point[1]}-${index}`}>
                    <span className="waypoint-index">{index + 1}</span>
                    <span className="waypoint-coords">x {km(point[0])} · y {km(point[1])}</span>
                    <button type="button" aria-label={`Quitar el punto ${index + 1}`} onClick={() => route.removePoint(index)}>×</button>
                  </li>)}
                </ol>}
                <p className="route-status" role="status">
                  {route.busy ? 'Calculando la ruta…' : !route.points.length ? 'Marca al menos dos puntos para trazar la ruta.'
                    : route.points.length === 1 ? 'Marca el destino para cerrar el tramo.'
                      : route.plan ? 'Ruta calculada.' : 'Esperando la malla…'}
                </p>
                {route.plan && <RouteSummary plan={route.plan} climb={route.options.climbPenalty ?? 0} />}
                <fieldset className="route-tolerance">
                  <legend>Terreno transitable</legend>
                  {(Object.keys(SEVERITY_PRESETS) as (keyof typeof SEVERITY_PRESETS)[]).map(key => <label key={key}>
                    <input type="radio" name="tolerance" checked={route.preset === key}
                      onChange={() => route.setPreset(key)} />
                    <span>{PRESET_LABELS[key]}</span>
                  </label>)}
                </fieldset>
                <label className="opacity">Peso de la pendiente <span>×{route.options.slopePenalty}</span>
                  <input type="range" min="0" max="12" step="1" value={route.options.slopePenalty}
                    aria-label="Peso de la pendiente en el costo" onChange={event => route.setPenalty(Number(event.target.value))} />
                </label>
                <label className="opacity" data-disabled={!route.hasElevation}>Peso del ascenso
                  <span>{route.options.climbPenalty ? `×${route.options.climbPenalty}` : 'sin coste'}</span>
                  <input type="range" min="0" max="12" step="1" value={route.options.climbPenalty ?? 0}
                    disabled={!route.hasElevation} aria-label="Peso del ascenso frente al rodeo"
                    onChange={event => route.setClimb(Number(event.target.value))} />
                </label>
                <p className="route-hint">{route.hasElevation
                  ? 'Con altura disponible el trazado suma los metros de subida: si rodear un cerro sale más barato, la ruta lo rodea.'
                  : 'Sin malla de altura el trazado solo puede valorar la pendiente superficial.'}</p>
                <button type="button" className="ghost" onClick={route.loadDemo}>Ver travesía de ejemplo</button>
              </>}
            <p className="route-footnote">Malla derivada de la capa «Pendientes · MDE CTX». Índice relativo, no grados
              validados: no apto para navegación real.</p>
          </section>

          <section className="layers-panel" aria-labelledby="layers-title">
            <div className="section-heading"><h2 id="layers-title">Capas del mapa</h2><span className="count">{layers.length}</span></div>
            {loading ? <p role="status">Cargando catálogo…</p> : error ? <p className="error" role="alert">{error}</p> : !layers.length ?
              <div className="empty-layers"><span aria-hidden="true">▱</span><h3>Tu atlas empieza aquí</h3>
                <p>Las capas aparecerán cuando añadamos los archivos y sus fichas al catálogo.</p></div> :
              <ul className="layer-list">{layers.map(layer => <li key={layer.id} className={selectedId === layer.id ? 'selected' : ''}>
                <div className="layer-row">
                  <input type="checkbox" aria-label={`Mostrar ${layer.name}`} checked={settings[layer.id]?.visible ?? true}
                    onChange={event => setSettings(previous => ({ ...previous,
                      [layer.id]: { ...previous[layer.id], visible: event.target.checked } }))} />
                  <button aria-pressed={selectedId === layer.id} onClick={() => setSelectedId(layer.id)}>{layer.name}</button>
                </div>
                <label className="opacity">Opacidad <span>{settings[layer.id]?.opacity ?? 100}%</span>
                  <input type="range" min="0" max="100" value={settings[layer.id]?.opacity ?? 100}
                    aria-label={`Opacidad de ${layer.name}`} onChange={event => setSettings(previous => ({ ...previous,
                      [layer.id]: { ...previous[layer.id], opacity: Number(event.target.value) } }))} />
                </label>
                <p className={statuses[layer.id] === 'error' ? 'error image-status' : 'image-status'}
                  role={statuses[layer.id] === 'error' ? 'alert' : 'status'}>
                  {statusLabels[statuses[layer.id] ?? 'loading']}</p>
              </li>)}</ul>}
          </section>
          <section className="info-panel" aria-labelledby="info-title">
            <span className="eyebrow">CONOCE TUS DATOS</span>
            <h2 id="info-title">{selected?.name ?? 'Cada imagen tiene una historia'}</h2>
            {selected ? <>
              <p>{selected.description}</p>
              <dl>{[
                ['Misión', selected.mission], ['Instrumento', selected.instrument],
                ['Resolución', selected.resolution], ['Fecha', selected.date],
                ['Licencia', selected.license], ['Limitaciones', selected.limitations],
              ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
              <a href={selected.source} target="_blank" rel="noreferrer">Consultar fuente ↗</a>
            </> : <p>Selecciona una capa para consultar su origen, resolución y limitaciones. Sin fuentes ocultas.</p>}
          </section>
          <div className="terrain-note" id="terrain-note"><span className="tag">PRÓXIMAMENTE · 3D</span>
            <p>Explorar el relieve requerirá un modelo de elevación validado.</p></div>
        </aside>
        <MapView layers={layers} settings={settings} onStatus={onStatus} route={route.plan} points={route.points}
          adding={route.adding} onMapClick={point => route.addPoint(point)} />
      </main>
      <button type="button" className="panels-toggle" aria-expanded={panelsOpen} aria-controls="workspace-panels"
        onClick={() => setPanelsOpen(!panelsOpen)}>{panelsOpen ? '× Cerrar' : '☰ Ruta'}</button>
      <footer><span><span className="dot" /> Prototipo en construcción · Sin datos científicos cargados automáticamente</span>
        <span>Exploración y educación. No apto para navegación real.</span></footer>
    </div>
  )
}