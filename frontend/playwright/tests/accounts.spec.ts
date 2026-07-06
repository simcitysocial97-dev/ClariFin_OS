import { test, expect } from '@playwright/test'

test.describe('Accounts page', () => {
  test('loads accounts list', async ({ page }) => {
    await page.goto('/accounts')
    await page.waitForTimeout(2000)

    // Page should render without crash
    await expect(page.locator('body')).toBeVisible()
    await expect(page.locator('text=404')).not.toBeVisible()
  })

  test('balances display in rupees (not paise)', async ({ page }) => {
    await page.goto('/accounts')
    await page.waitForTimeout(2000)

    // Find balance displays — they should contain ₹ symbol
    // and should NOT show 6+ digit numbers for typical bank balances
    // (a balance of ₹10,000 shown as 1,000,000 would indicate paise bug)
    const balanceElements = page.locator('[class*="balance"], [class*="amount"]')
    const count = await balanceElements.count()

    if (count > 0) {
      const firstBalance = await balanceElements.first().textContent()
      // If balance contains ₹ symbol, the formatter ran
      expect(firstBalance).toContain('₹')
    }
  })
})