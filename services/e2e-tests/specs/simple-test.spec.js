import { test, expect } from '@playwright/test';

test('Simple Authentik authentication test', async ({ page }) => {
  console.log('Starting simple authentication test...');
  
  // Navigate directly to Authentik login page
  console.log('Navigating to Authentik admin interface...');
  await page.goto('http://zoi.local:9000/if/admin/', { 
    waitUntil: 'domcontentloaded',
    timeout: 15000 
  });
  
  console.log('Current URL:', page.url());
  
  // Check if we can see the Authentik interface
  await page.waitForTimeout(2000);
  
  // Take a screenshot for debugging
  await page.screenshot({ path: 'test-results/simple-test-screenshot.png' });
  
  console.log('Page title:', await page.title());
  console.log('Test completed - check screenshot for results');
}); 