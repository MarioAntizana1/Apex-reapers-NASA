import { expect, test } from '@playwright/test'

const map = (page: import('@playwright/test').Page) => page.getByRole('region', { name: 'Mapa de Jezero' })

test.beforeEach(async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/')
  await page.locator('.panels-toggle').click()
  await expect(page.locator('.sidebar')).toBeVisible()
})

test('la travesía de ejemplo calcula la ruta y la dibuja sobre el mapa', async ({ page }) => {
  await expect(page.getByText('Capa cargada', { exact: true })).toBeVisible()
  const before = await map(page).screenshot()

  await page.getByRole('button', { name: 'Ver travesía de ejemplo' }).click()
  await expect(page.getByText('Ruta calculada.', { exact: true })).toBeVisible({ timeout: 20_000 })
  await expect(page.getByText(/línea recta/)).toBeVisible()
  await expect(page.getByText(/\+\d+ %/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Quitar el punto 1' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Quitar el punto 2' })).toBeVisible()

  await expect.poll(async () => (await map(page).screenshot()).equals(before), { timeout: 10_000 }).toBe(false)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await page.screenshot({ path: 'test-results/route-demo.png', fullPage: true })
})

test('los clics en el mapa añaden puntos y disparan el cálculo', async ({ page }) => {
  await expect(page.getByText(/Marca al menos dos puntos/)).toBeVisible()
  await page.getByRole('button', { name: 'Marcar inicio' }).click()
  await expect(page.getByText('Haz clic en el mapa para añadir el siguiente punto')).toBeVisible()

  const box = await map(page).boundingBox()
  if (!box) throw new Error('El mapa no tiene medidas.')
  await page.mouse.click(box.x + box.width * 0.45, box.y + box.height * 0.55)
  await expect(page.getByText('Marca el destino para cerrar el tramo.')).toBeVisible()

  await page.mouse.click(box.x + box.width * 0.6, box.y + box.height * 0.35)
  await expect(page.getByRole('button', { name: 'Quitar el punto 2' })).toBeVisible()
  await expect(page.getByText(/Ruta calculada\.|Sin trazado con esta tolerancia\./)).toBeVisible({ timeout: 20_000 })

  await page.getByRole('button', { name: 'Deshacer' }).click()
  await expect(page.getByRole('button', { name: 'Quitar el punto 2' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Borrar' }).click()
  await expect(page.getByText(/Marca al menos dos puntos/)).toBeVisible()
  await page.screenshot({ path: 'test-results/route-clicks.png', fullPage: true })
})

test('pide la malla de pendientes y muestra que no es navegación real', async ({ page }) => {
  const grid = page.waitForResponse('**/terrain/terrain.json')
  await page.reload()
  expect((await grid).ok()).toBe(true)
  await page.locator('.panels-toggle').click()
  await expect(page.getByText(/Índice relativo, no grados validados/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Ver travesía de ejemplo' })).toBeVisible()
})