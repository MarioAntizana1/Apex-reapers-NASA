import { expect, test } from '@playwright/test'

const testLayer = {
  id: 'test', name: 'Imagen de prueba', url: 'maps/test.svg',
  extent: [-100, -100, 100, 100], source: 'https://science.nasa.gov/',
  description: 'Imagen sintética de prueba.', mission: 'Prueba', instrument: 'Prueba',
  resolution: 'No aplica', date: 'No aplica', license: 'Prueba', limitations: 'Solo prueba',
}

test.beforeEach(async ({ page }) => {
  await page.route('**/layers.json', route => route.fulfill({ json: { layers: [] } }))
})

test('presenta Apex-Mars y atribuye el equipo Apex-Reapers', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle('Apex-Mars · Jezero')
  await expect(page.getByRole('link', { name: 'Apex-Mars, inicio' })).toBeVisible()
  await expect(page.getByText('Apex-Reapers', { exact: true })).toBeVisible()
})

test('el catálogo local carga sus imágenes reales sin errores', async ({ page }) => {
  await page.unroute('**/layers.json')
  const response = page.waitForResponse('**/layers.json')
  await page.goto('/')
  const catalog = await (await response).json()
  expect(catalog.layers.length).toBeGreaterThan(0)
  for (const layer of catalog.layers) {
    await page.getByRole('checkbox', { name: `Mostrar ${layer.name}`, exact: true }).check()
  }
  await expect(page.getByText('Capa cargada', { exact: true })).toHaveCount(catalog.layers.length)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('checkbox', { name: 'Mostrar Jezero · ortomosaico CTX' })).toBeVisible()
  await page.screenshot({ path: 'test-results/local-catalog.png', fullPage: true })
})

test('sin recursos muestra el estado vacío y no promete 3D', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Mapa pendiente de cargar' })).toBeVisible()
  await expect(page.getByRole('button', { name: '3D' })).toBeDisabled()
  await expect(page.getByRole('region', { name: 'Mapa de Jezero' })).toBeVisible()
})

test('carga una imagen, muestra su ficha y permite ocultarla y cambiar opacidad', async ({ page }) => {
  await page.route('**/layers.json', route => route.fulfill({
    json: { layers: [testLayer] },
  }))
  await page.route('**/maps/test.svg', route => route.fulfill({
    contentType: 'image/svg+xml',
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="tan"/></svg>',
  }))
  await page.goto('/')
  await expect(page.getByText('Imagen sintética de prueba.')).toBeVisible()
  await expect(page.getByText('Capa cargada')).toBeVisible()
  const map = page.getByRole('region', { name: 'Mapa de Jezero' })
  const opaqueMap = await map.screenshot()
  await page.getByRole('slider', { name: 'Opacidad de Imagen de prueba' }).fill('40')
  await expect(page.getByText('40%')).toBeVisible()
  await expect.poll(async () => (await map.screenshot()).equals(opaqueMap)).toBe(false)
  const translucentMap = await map.screenshot()
  await page.getByRole('checkbox', { name: 'Mostrar Imagen de prueba' }).uncheck()
  await expect(page.getByRole('checkbox')).not.toBeChecked()
  await expect.poll(async () => (await map.screenshot()).equals(translucentMap)).toBe(false)
  await expect(page.getByRole('button', { name: 'Restablecer vista' })).toBeEnabled()
})

test('informa de una imagen ausente junto a su capa', async ({ page }) => {
  await page.route('**/layers.json', route => route.fulfill({ json: { layers: [testLayer] } }))
  await page.route('**/maps/test.svg', route => route.fulfill({ status: 404 }))
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('No se pudo cargar la imagen')
  await expect(page.getByText('Capa cargada')).toHaveCount(0)
})

test('informa del fallo del catálogo', async ({ page }) => {
  await page.route('**/layers.json', route => route.fulfill({ status: 503 }))
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('No se pudo cargar')
})

test('el estado vacío es usable en móvil y no desborda la pantalla', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Mapa pendiente de cargar' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.screenshot({ path: 'test-results/mobile.png', fullPage: true })
})

test('la interfaz de escritorio no genera errores de JavaScript', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Mapa pendiente de cargar' })).toBeVisible()
  await page.screenshot({ path: 'test-results/desktop.png', fullPage: true })
  expect(errors).toEqual([])
})
