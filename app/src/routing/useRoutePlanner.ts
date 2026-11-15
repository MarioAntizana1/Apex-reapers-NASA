import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { DEMO_POINTS } from './demo'
import {
  DEFAULT_CLIMB_PENALTY, DEFAULT_DESCENT_FACTOR, planRoute, SEVERITY_PRESETS,
  type PlanOptions, type RoutePlan, type RoutePoint, type SeverityPreset,
} from './planner'
import { loadTerrainField, type TerrainField, type TerrainMeta } from './terrain'

export type PlannerState = 'cargando' | 'listo' | 'error'

export interface RouteController {
  state: PlannerState
  error: string
  meta: TerrainMeta | null
  /** Hay malla de altura: se puede comparar subir contra rodear. */
  hasElevation: boolean
  points: RoutePoint[]
  plan: RoutePlan | null
  busy: boolean
  options: PlanOptions
  preset: SeverityPreset
  adding: boolean
  setPreset: (preset: SeverityPreset) => void
  setPenalty: (penalty: number) => void
  setClimb: (climb: number) => void
  setAdding: (value: boolean) => void
  addPoint: (point: RoutePoint) => void
  removePoint: (index: number) => void
  undo: () => void
  clear: () => void
  loadDemo: () => void
}

const DEBOUNCE_MS = 80

/**
 * Carga las mallas de pendiente y altura, las entrega a un Web Worker y pide una
 * nueva ruta cada vez que cambian los puntos o el criterio de terreno (con un
 * pequeño retardo para no recalcular en cada clic del deslizador).
 */
export function useRoutePlanner(): RouteController {
  const [state, setState] = useState<PlannerState>('cargando')
  const [error, setError] = useState('')
  const [meta, setMeta] = useState<TerrainMeta | null>(null)
  const [hasElevation, setHasElevation] = useState(false)
  const [points, setPoints] = useState<RoutePoint[]>([])
  const [plan, setPlan] = useState<RoutePlan | null>(null)
  const [busy, setBusy] = useState(false)
  const [preset, setPresetState] = useState<SeverityPreset>('estandar')
  const [penalty, setPenaltyState] = useState(6)
  const [climb, setClimbState] = useState(DEFAULT_CLIMB_PENALTY)
  const [adding, setAdding] = useState(false)

  const worker = useRef<Worker | null>(null)
  const fallback = useRef<TerrainField | null>(null)
  const requestId = useRef(0)

  useEffect(() => {
    const controller = new AbortController()
    let disposed = false
    async function start() {
      try {
        const field = await loadTerrainField(import.meta.env.BASE_URL, controller.signal)
        if (disposed) return
        setMeta(field.meta)
        setHasElevation(Boolean(field.elevation))
        try {
          const instance = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' })
          instance.onmessage = event => {
            const data = event.data as { type: string; requestId?: number; plan?: RoutePlan; message?: string }
            if (data.type === 'result' && data.requestId === requestId.current) {
              setPlan(data.plan ?? null)
              setBusy(false)
            } else if (data.type === 'error' && data.requestId === requestId.current) {
              setError(data.message ?? 'El planificador falló.')
              setState('error')
              setBusy(false)
            }
          }
          // Copias aparte: los búferes transferidos quedan inertes en este hilo y el
          // cálculo de reserva sigue necesitando los datos originales.
          const severity = field.severity.slice()
          const elevation = field.elevation ? field.elevation.slice() : null
          const transfer: Transferable[] = [severity.buffer]
          if (elevation) transfer.push(elevation.buffer)
          instance.postMessage({
            type: 'grid', meta: field.meta, severity: severity.buffer,
            elevation: elevation ? elevation.buffer : null, metresPerIndex: field.metresPerIndex,
          }, transfer)
          worker.current = instance
        } catch {
          // Sin Web Worker el cálculo sigue en el hilo principal, con los mismos datos.
        }
        fallback.current = field
        setState('listo')
      } catch (reason) {
        if (disposed) return
        setError(reason instanceof Error ? reason.message : 'No se pudo cargar la malla de pendientes.')
        setState('error')
      }
    }
    void start()
    return () => {
      disposed = true
      controller.abort()
      worker.current?.terminate()
      worker.current = null
    }
  }, [])

  const options = useMemo<PlanOptions>(() => ({
    maxSeverity: SEVERITY_PRESETS[preset],
    slopePenalty: penalty,
    climbPenalty: climb,
    descentFactor: DEFAULT_DESCENT_FACTOR,
  }), [preset, penalty, climb])

  useEffect(() => {
    if (state !== 'listo') return
    if (points.length < 2) {
      setPlan(null)
      setBusy(false)
      return
    }
    const handle = setTimeout(() => {
      const id = requestId.current + 1
      requestId.current = id
      setBusy(true)
      if (worker.current) {
        worker.current.postMessage({ type: 'plan', requestId: id, points, options })
        return
      }
      const field = fallback.current
      if (!field) {
        setBusy(false)
        return
      }
      try {
        const next = planRoute(field, points, options)
        if (requestId.current === id) setPlan(next)
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : 'No se pudo calcular la ruta.')
        setState('error')
      } finally {
        setBusy(false)
      }
    }, DEBOUNCE_MS)
    return () => clearTimeout(handle)
  }, [points, options, state])

  const addPoint = useCallback((point: RoutePoint) => {
    setPoints(previous => [...previous, point])
  }, [])

  const removePoint = useCallback((index: number) => {
    setPoints(previous => previous.filter((_, position) => position !== index))
  }, [])

  const undo = useCallback(() => {
    setPoints(previous => previous.slice(0, -1))
  }, [])

  const clear = useCallback(() => {
    setPoints([])
    setPlan(null)
  }, [])

  const loadDemo = useCallback(() => {
    setPoints(DEMO_POINTS.map(point => [point[0], point[1]] as RoutePoint))
    setAdding(false)
  }, [])

  const setPreset = useCallback((value: SeverityPreset) => setPresetState(value), [])
  const setPenalty = useCallback((value: number) => setPenaltyState(value), [])
  const setClimb = useCallback((value: number) => setClimbState(value), [])

  return {
    state, error, meta, hasElevation, points, plan, busy, options, preset, adding,
    setPreset, setPenalty, setClimb, setAdding, addPoint, removePoint, undo, clear, loadDemo,
  }
}
