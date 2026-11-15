# Integración del planificador de rutas en la app nueva (3D + EVA)

Esta guía existe porque el código de rutas vive en `app/` (rama `feat/rutas-pendiente-relieve`)
y la app nueva —la del deploy de `gh-pages`: visor 3D, capacidades del traje, paradas
científicas, recursos CO₂/comida/oxígeno— se publica **solo compilada**. Para llevarle el
planificador hay que tocar cuatro puntos en su fuente.

## Qué se copia tal cual (no depende de React ni de OpenLayers)

| Archivo | Qué hace |
| --- | --- |
| `src/routing/planner.ts` | A\* de 8 direcciones sin cortar esquinas sobre malla de ~60 m. Coste = distancia `1 + slopePenalty·(índice/255)²` + metros equivalentes de subida (bajar cuenta `0,35`). Devuelve ruta, ascenso, descenso, pendiente máxima, células visitadas y ms. |
| `src/routing/terrain.ts` | Carga `terrain.json` + los dos PNG (altura y pendiente) en `Float32Array`, convierte coordenada ↔ celda. |
| `src/routing/worker.ts` | Envuelve el planificador en un Web Worker; recibe la malla una vez y responde a cada petición. |
| `src/routing/useRoutePlanner.ts` | Hook de React con debounce de 80 ms, estado `plan/loading/error` y `setClimb`. Es lo único atado a React. |
| `public/terrain/*` | `elevation_60m.png`, `slope_index_60m.png`, `terrain.json`. Regenerables con `scripts/build_terrain_grids.py` (relleno en dos etapas + desenfoque) y `scripts/build_slope_index.py`. |

## Los cuatro puntos de enganche

1. **Assets**: copiar `public/terrain/` a `public/terrain/` de la app nueva (misma estructura y
   `extent` del ortofotomosaico CTX de Jezero, así que las coordenadas coinciden).
2. **Malla**: instanciar `useRoutePlanner()` una vez en el componente que guarda la ruta
   (base y paradas). El hook ya carga la malla al montar.
3. **Ruta**: pasar `[{x, y}, …]` en coordenadas del mapa (`EPSG:3857`, las mismas de `layers.json`).
   `planRoute` devuelve la polilínea simplificada, lista para añadir como capa vectorial.
4. **UI**: mostrar `distance`, `ascent`, `descentMetres`, `maxSeverity`, `savedAscent`,
   `detourForClimb`, `elapsed` y el veredicto. El slider «Peso del ascenso» (0–12) es lo que
   permite comparar subir la pendiente frente a rodearla; con 0 el trazado ignora la altura.

## Por qué el ahorro se mide contra una ruta base

`planRoute(..., { climbPenalty: 0 })` se ejecuta una segunda vez cuando el peso es > 0 y sirve de
referencia: así el ahorro (`savedAscent`) se mide contra otra ruta **transitable**, no contra la
línea recta, que puede cruzar paredes del cráter. Cuesta ~2 ms extra sobre ~6 ms.

## Verificación de referencia (build actual)

| Peso | Ruta | Ascenso | Pendiente máx. | Celdas · tiempo | Veredicto |
| --- | --- | --- | --- | --- | --- |
| 0 | 3,8 km (+33 %) | 910 m | 152/255 | 2.000 · 2 ms | sin peso de ascenso solo manda la distancia |
| 4 | 3,8 km (+31 %) | 816 m | 152/255 | 3.164 · 7 ms | rodea el relieve sin pagar ruta: ahorra 94 m |
| 12 | 4,8 km (+66 %) | 298 m | 176/255 | 4.665 · 7 ms | rodea el relieve: +944 m de ruta por 612 m de ascenso |

`tsc --noEmit` limpio, 35 tests vitest en verde, `npm run build` OK y
`tests/route.spec.ts` (Playwright) comprueba que la ruta se dibuja sobre el mapa.
