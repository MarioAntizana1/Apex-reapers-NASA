import type { RoutePoint } from './planner'

/**
 * Travesía de ejemplo sobre Jezero, elegida buscando una loma de ~60 m: los dos
 * extremos quedan a 2,9 km en línea recta, pero la recta trepa por la ladera.
 * Sin coste de ascenso el trazado se pega a la pendiente (≈3,8 km y 910 m de
 * subida); al subir el peso del ascenso la rodea por la falda (≈4,8 km y 300 m).
 * Es el par donde el deslizador del panel muestra el cambio con más claridad.
 */
export const DEMO_POINTS: RoutePoint[] = [
  [5193, -32668],
  [8074, -32668],
]