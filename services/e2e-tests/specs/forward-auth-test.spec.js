const { test, expect } = require('@playwright/test');

test.describe('Forward Auth Tests', () => {
  
  test('should test forward auth redirect behavior', async ({ page }) => {
    console.log('Testing forward auth behavior...');
    
    // Try to access Dashy via Traefik (should redirect to auth)
    try {
      await page.goto('http://dashy.zoi.local', { 
        waitUntil: 'networkidle',
        timeout: 10000 
      });
      
      console.log('Current URL after navigation:', page.url());
      
      // Take a screenshot to see what we got
      await page.screenshot({ path: 'test-results/forward-auth-result.png' });
      
      // Check if we were redirected to Authentik
      if (page.url().includes('authentik') || page.url().includes('auth')) {
        console.log('✅ Successfully redirected to authentication');
        
        // Look for login form
        const loginForm = await page.locator('input[name="uid_field"]');
        if (await loginForm.isVisible()) {
          console.log('✅ Login form is visible');
        }
      } else if (page.url().includes('dashy')) {
        console.log('ℹ️ Already authenticated or auth bypassed');
      } else {
        console.log('⚠️ Unexpected redirect target:', page.url());
      }
      
    } catch (error) {
      console.log('❌ Forward auth test failed:', error.message);
      
      // Take a screenshot of the error state
      await page.screenshot({ path: 'test-results/forward-auth-error.png' });
      
      // If it's a timeout, that might be expected
      if (error.message.includes('Timeout')) {
        console.log('This might indicate an authentication loop or configuration issue');
      }
      
      throw error;
    }
  });
  
  test('should test direct Authentik login', async ({ page }) => {
    console.log('Testing direct Authentik login...');
    
    // Go directly to Authentik login
    await page.goto('http://zoi.local:9000/if/flow/default-authentication-flow/');
    
    console.log('Current URL:', page.url());
    await page.screenshot({ path: 'test-results/authentik-login-direct.png' });
    
    // Try to fill in login form if it exists
    try {
      await page.waitForSelector('input[name="uid_field"]', { timeout: 5000 });
      
      // Fill in credentials
      await page.fill('input[name="uid_field"]', 'admin');
      await page.fill('input[name="password"]', 'change-me-authentik-admin');
      
      console.log('✅ Login form found and filled');
      
      // Take a screenshot before submitting
      await page.screenshot({ path: 'test-results/authentik-login-filled.png' });
      
    } catch (error) {
      console.log('⚠️ Login form not found or different structure:', error.message);
    }
  });
  
}); 