const C = window.Cesium
const status = document.querySelector('#estado')

async function load(path) {
  const response = await fetch(`./datos/${path}`)
  if (!response.ok) throw new Error(`No se pudo cargar ${path}`)
  return response
}

async function start() {
  const { relieve, imagenes, destinos } = await (await load('bloques/indice.json')).json()
  const ellipsoid = new C.Ellipsoid(3396190, 3396190, 3396190)
  C.Ellipsoid.default = ellipsoid
  const scheme = new C.GeographicTilingScheme({ ellipsoid })
  const size = relieve.tamano
  const regions = relieve.zonas.map(zone => ({ level: zone.nivel, rect: C.Rectangle.fromDegrees(...zone.bbox) }))
  function available(x, y, level) {
    if (level <= relieve.global) return true
    const tile = scheme.tileXYToRectangle(x, y, level)
    return regions.some(({ level: max, rect }) => level <= max &&
      tile.west < rect.east && tile.east > rect.west && tile.south < rect.north && tile.north > rect.south)
  }
  const provider = new C.CustomHeightmapTerrainProvider({
    tilingScheme: scheme, width: size, height: size, callback: () => undefined,
  })
  provider.getTileDataAvailable = available
  provider.requestTileGeometry = (x, y, level, request) => {
    const resource = new C.Resource({ url: `./datos/bloques/relieve/${level}/${x}/${y}.bin`, request })
    return resource.fetchArrayBuffer()?.then(buffer => {
      if (buffer.byteLength !== 2 * size * size) throw new Error('Bloque de relieve inválido')
      const view = new DataView(buffer)
      const heights = new Int16Array(size * size)
      for (let i = 0; i < heights.length; i++) heights[i] = view.getInt16(i * 2, true)
      let childTileMask = 0
      for (let dy = 0; dy < 2; dy++) {
        for (let dx = 0; dx < 2; dx++) {
          if (available(2 * x + dx, 2 * y + dy, level + 1)) childTileMask |= 1 << (2 * (1 - dy) + dx)
        }
      }
      return new C.HeightmapTerrainData({ buffer: heights, width: size, height: size, childTileMask })
    })
  }
  const globe = new C.Globe(ellipsoid)
  globe.depthTestAgainstTerrain = true
  globe.showGroundAtmosphere = false
  globe.tileCacheSize = 160
  globe.baseColor = C.Color.fromCssColorString('#a7755b')
  const viewer = new C.CesiumWidget('mapa', {
    ellipsoid, globe, terrainProvider: provider, baseLayer: false, skyBox: false,
    skyAtmosphere: false, shadows: false, requestRenderMode: true,
  })
  viewer.scene.backgroundColor = C.Color.fromCssColorString('#100c0b')
  viewer.scene.fog.enabled = false
  const controls = viewer.scene.screenSpaceCameraController
  controls.minimumZoomDistance = 120
  controls.maximumZoomDistance = 16000000
  for (const { id, bbox, nivel, columnas } of imagenes) {
    const rectangle = C.Rectangle.fromDegrees(...bbox)
    globe.imageryLayers.addImageryProvider(new C.UrlTemplateImageryProvider({
      url: `./datos/bloques/imagen/${id}/{z}/{x}/{y}.webp`, rectangle, maximumLevel: nivel,
      tilingScheme: new C.GeographicTilingScheme({ ellipsoid, rectangle, numberOfLevelZeroTilesX: columnas }),
    }))
  }
  const reduced = matchMedia('(prefers-reduced-motion: reduce)')
  const views = {
    global: [73, 16, 8400000, -90, 'Marte global · relieve MOLA'],
    jezero: [77.46, 18.35, 16500, -68, 'Jezero · relieve CTX'],
    borde: [77.96, 18.35, 16500, -68, 'Alrededores de Jezero · relieve MOLA'],
  }
  function go(view, duration) {
    const [lon, lat, height, pitch, label] = views[view]
    viewer.camera.cancelFlight()
    status.textContent = 'Moviendo cámara…'
    const options = {
      destination: C.Cartesian3.fromDegrees(lon, lat, height, ellipsoid),
      orientation: { heading: 0, pitch: C.Math.toRadians(pitch), roll: 0 },
    }
    const finish = () => { status.textContent = label }
    if (duration === 0 || reduced.matches) {
      viewer.camera.setView(options)
      finish()
    } else {
      viewer.camera.flyTo({ ...options, duration, complete: finish,
        ...(view === 'borde' && viewer.camera.positionCartographic.height < 60000 ? { maximumHeight: height } : {}),
      })
    }
  }
  for (const view of Object.keys(views)) {
    document.getElementById(view).onclick = () => go(view, view === 'global' ? 2.8 : view === 'jezero' ? 4.2 : 2.6)
  }
  const pins = viewer.scene.primitives.add(new C.PointPrimitiveCollection())
  const distance = new C.DistanceDisplayCondition(90000, 16000000)
  for (const { id, nombre, lon, lat } of destinos) {
    if (id !== 'jezero') views[id] = [lon, lat, 420000, -80, nombre]
    const button = document.createElement('button')
    button.type = 'button'
    button.textContent = nombre
    button.onclick = () => go(id, 3.1)
    document.querySelector('#destinos').append(button)
    pins.add({
      id, position: C.Cartesian3.fromDegrees(lon, lat, 25000, ellipsoid),
      pixelSize: 9, color: C.Color.fromCssColorString('#ffd19c'),
      outlineColor: C.Color.fromCssColorString('#392318'), outlineWidth: 2,
      distanceDisplayCondition: distance,
    })
  }
  viewer.screenSpaceEventHandler.setInputAction(({ position }) => {
    const picked = viewer.scene.pick(position)
    if (picked?.collection === pins || picked?.primitive instanceof C.PointPrimitive) go(picked.id, 3.1)
  }, C.ScreenSpaceEventType.LEFT_CLICK)
  go('global', 0)
}

start().catch(error => {
  status.textContent = `El visor no pudo iniciar: ${error.message}`
  console.error(error)
})
