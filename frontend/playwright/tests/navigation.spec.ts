import { test, expect } from '@playwright/test'

const ACTIVE_ROUTES = ['/', '/dashboard', '/accounts', '/cards', '/settings', '/transactions']

const REMOVED_ROUTES = [
  '/loans', '/investments', '/imports', '/statements', '/reconciliation',
  '/categories', '/income', '/income-sources', '/export', '/snapshots',
  '/networth', '/cashflow', '/analytics', '/projections', '/recurring',
  '/audit', '/behavior', '/test/metadata',
]

const REDIRECT_ROUTES = [
  { from: '/projections', to: '/dashboard' },
  { from: '/import', to: '/transactions' },
  { from: '/imports', to: '/transactions' },
]

test.describe('Active routes render without error', () => {
  for (const route of ACTIVE_ROUTES) {
    test(`${route} loads without 404 or crash`, async ({ page }) => {
      const response = await page.goto(route)

      // No 404
      expect(response?.status()).not.toBe(404)

      // No error boundary triggered
      await expect(page.locator('text=Something went wrong')).not.toBeVisible()
      await expect(page.locator('text=404')).not.toBeVisible()

      // Page has content (not blank)
      const bodyText = await page.locator('body').textContent()
      expect(bodyText?.trim().length).toBeGreaterThan(0)
    })
  }
})

test.describe('Removed routes return 404 or redirect', () => {
  for (const route of REMOVED_ROUTES) {
    test(`${route} does not return live content`, async ({ page }) => {
      const response = await page.goto(route)
      // Should either 404 or redirect — not serve stale content
      const is404 = response?.status() === 404
      const isRedirected = page.url() !== `http://localhost:3000${route}`
      expect(is404 || isRedirected).toBe(true)
    })
  }
})

test.describe('Redirect routes go to correct destination', () => {
  for (const { from, to } of REDIRECT_ROUTES) {
    test(`${from} redirects to ${to}`, async ({ page }) => {
      await page.goto(from)
      await expect(page).toHaveURL(new RegExp(to))
    })
  }
})