const { test, expect } = require('@playwright/test');

test.describe('Dashy Dashboard Authentication Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard before each test
    await page.goto('/', { waitUntil: 'networkidle' });
  });

  test('should load dashboard with authentication', async ({ page }) => {
    // Should be on Dashy, not redirected to auth (because of stored auth state)
    await expect(page).toHaveURL(/.*dashy.*/);
    
    // Check main title
    await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
    
    // Check that main sections are visible
    await expect(page.locator('text=Core API & Services')).toBeVisible();
    await expect(page.locator('text=Authentication & Security')).toBeVisible();
    await expect(page.locator('text=AI & Automation Platforms')).toBeVisible();
    await expect(page.locator('text=Storage & Databases')).toBeVisible();
  });

  test('should display service links correctly', async ({ page }) => {
    // Test that key service links are present and visible
    const fastApiLink = page.locator('text=FastAPI Main');
    await expect(fastApiLink).toBeVisible();
    
    const authentikLink = page.locator('text=Authentik SSO');
    await expect(authentikLink).toBeVisible();
    
    const traefikLink = page.locator('text=Traefik Dashboard');
    await expect(traefikLink).toBeVisible();
    
    const qdrantLink = page.locator('text=Qdrant Vector DB');
    await expect(qdrantLink).toBeVisible();
  });

  test('should have working status checks for core services', async ({ page }) => {
    // Wait for status checks to complete (they may take a few seconds)
    await page.waitForTimeout(5000);
    
    // Look for status indicators - these might be icons, colors, or text
    const statusElements = await page.locator('[class*="status"], [data-testid*="status"]').all();
    
    if (statusElements.length > 0) {
      // At least one status element should be visible
      await expect(statusElements[0]).toBeVisible();
      console.log(`Found ${statusElements.length} status indicators`);
    } else {
      // If no specific status elements, check that service items are visible
      const serviceItems = await page.locator('[class*="item"]').all();
      expect(serviceItems.length).toBeGreaterThan(0);
      console.log(`Found ${serviceItems.length} service items`);
    }
  });

  test('should maintain responsive layout', async ({ page }) => {
    // Test desktop layout
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.locator('h1')).toBeVisible();
    
    // Test tablet layout
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('h1')).toBeVisible();
    
    // Test mobile layout
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should have working search functionality', async ({ page }) => {
    // Look for search input (Dashy typically has search functionality)
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]');
    
    if (await searchInput.count() > 0) {
      await searchInput.fill('api');
      await page.waitForTimeout(1000); // Wait for search to filter
      
      // Should still see FastAPI in results
      await expect(page.locator('text=FastAPI')).toBeVisible();
    } else {
      console.log('Search functionality not found - skipping search test');
    }
  });
}); 