import { planRoute, type PlanOptions, type RoutePoint } from './planner'
import type { TerrainField } from './terrain'

/** Peticiones que la interfaz envía al hilo de cálculo. */
export type PlannerRequest =
  | { type: 'grid'; meta: TerrainField['meta']; severity: ArrayBuffer; elevation: ArrayBuffer | null; metresPerIndex: number }
  | { type: 'plan'; requestId: number; points: RoutePoint[]; options: PlanOptions }

interface PlannerScope {
  onmessage: ((event: MessageEvent<PlannerRequest>) => void) | null
  postMessage: (message: unknown) => void
}

const scope = self as unknown as PlannerScope

let field: TerrainField | null = null

scope.onmessage = (event: MessageEvent<PlannerRequest>) => {
  const request = event.data
  if (request.type === 'grid') {
    field = {
      meta: request.meta,
      severity: new Uint8Array(request.severity),
      elevation: request.elevation ? new Uint8Array(request.elevation) : null,
      metresPerIndex: request.metresPerIndex,
    }
    scope.postMessage({ type: 'ready' })
    return
  }
  if (request.type !== 'plan') return
  if (!field) {
    scope.postMessage({ type: 'error', requestId: request.requestId, message: 'La malla de terreno aún no está lista.' })
    return
  }
  try {
    const plan = planRoute(field, request.points, request.options)
    scope.postMessage({ type: 'result', requestId: request.requestId, plan })
  } catch (reason) {
    scope.postMessage({
      type: 'error',
      requestId: request.requestId,
      message: reason instanceof Error ? reason.message : 'El planificador falló sin detalle.',
    })
  }
}