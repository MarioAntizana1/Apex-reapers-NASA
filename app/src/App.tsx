import { useCallback, useEffect, useState } from 'react'
import { MapView, type ImageStatus, type LayerState } from './MapView'
import { parseLayers, type MapImage } from './layers'
import './styles.css'

export default function App() {
  const [layers, setLayers] = useState<MapImage[]>([])
  const [settings, setSettings] = useState<Record<string, LayerState>>({})
  const [statuses, setStatuses] = useState<Record<string, ImageStatus>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
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

  return (
    <div className="app">
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
        <aside className="sidebar" aria-label="Capas e información">
          <div className="panel-title"><span className="eyebrow">EXPLORA JEZERO</span><h1>Una capa a la vez.</h1>
            <p>Descubre el terreno y la ciencia que lo hace especial.</p></div>
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
        <MapView layers={layers} settings={settings} onStatus={onStatus} />
      </main>
      <footer><span><span className="dot" /> Prototipo en construcción · Sin datos científicos cargados automáticamente</span>
        <span>Exploración y educación. No apto para navegación real.</span></footer>
    </div>
  )
}
