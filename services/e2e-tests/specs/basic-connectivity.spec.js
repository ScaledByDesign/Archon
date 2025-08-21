const { test, expect } = require('@playwright/test');

test.describe('Basic Connectivity Tests', () => {
  
  test('should access Dashy directly via port 4001', async ({ page }) => {
    console.log('Testing direct access to Dashy...');
    
    // Access Dashy directly via its exposed port
    await page.goto('http://zoi.local:4001');
    
    // Wait for the page to load
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // Verify we can see the dashboard title
    const title = await page.locator('h1').textContent();
    console.log('Dashboard title:', title);
    
    expect(title).toContain('Dashy');
    
    // Take a screenshot for verification
    await page.screenshot({ path: 'test-results/dashy-direct-access.png' });
    
    console.log('✅ Direct access to Dashy successful!');
  });
  
  test('should access Authentik admin interface', async ({ page }) => {
    console.log('Testing access to Authentik admin...');
    
    // Access Authentik admin interface
    await page.goto('http://zoi.local:9000/if/admin/');
    
    // Wait for the admin interface to load
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Check if we can see Authentik interface
    const pageContent = await page.content();
    expect(pageContent).toContain('authentik');
    
    // Take a screenshot
    await page.screenshot({ path: 'test-results/authentik-admin-access.png' });
    
    console.log('✅ Access to Authentik admin successful!');
  });
  
  test('should check Traefik dashboard accessibility', async ({ page }) => {
    console.log('Testing access to Traefik dashboard...');
    
    // Access Traefik dashboard
    await page.goto('http://zoi.local:8080');
    
    // Wait for the dashboard to load
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Check if we can see Traefik dashboard
    const pageContent = await page.content();
    expect(pageContent.toLowerCase()).toContain('traefik');
    
    // Take a screenshot
    await page.screenshot({ path: 'test-results/traefik-dashboard-access.png' });
    
    console.log('✅ Access to Traefik dashboard successful!');
  });
  
}); 