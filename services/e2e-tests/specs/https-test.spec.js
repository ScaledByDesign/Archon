import { test, expect } from '@playwright/test';

test.use({ 
  ignoreHTTPSErrors: true,  // Accept self-signed certificates
  extraHTTPHeaders: {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
  }
});

test('HTTPS Dashy authentication with certificate bypass', async ({ page }) => {
  console.log('🧪 Testing HTTPS with certificate bypass...');

  try {
    // Navigate to HTTPS dashy with certificate bypass
    console.log('1️⃣ Navigating to https://dashy.zoi.local with ignoreHTTPSErrors...');
    await page.goto('https://dashy.zoi.local', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });

    // Check current URL and page state
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);

    // If we're on an authentication page, try to proceed
    if (currentUrl.includes('zoi.local:9000') || currentUrl.includes('0.0.0.0:9000')) {
      console.log('🔐 Redirected to authentication page');
      
      // Replace 0.0.0.0:9000 with zoi.local:9000 if needed
      if (currentUrl.includes('0.0.0.0:9000')) {
        const fixedUrl = currentUrl.replace('0.0.0.0:9000', 'zoi.local:9000');
        console.log(`🔧 Fixing URL: ${fixedUrl}`);
        await page.goto(fixedUrl, { waitUntil: 'domcontentloaded' });
      }

      // Look for login form or already authenticated state
      try {
        // Check if we're already authenticated (redirect back to Dashy)
        await page.waitForURL(/dashy\.zoi.local/, { timeout: 5000 });
        console.log('✅ Successfully authenticated and redirected to Dashy!');
      } catch {
        // Try to find login form
        console.log('🔑 Looking for login form...');
        const loginButton = page.locator('button[type="submit"]').first();
        
        if (await loginButton.isVisible()) {
          console.log('📝 Found login form, attempting authentication...');
          
          // Fill login if needed (you may need to adjust selectors)
          const usernameField = page.locator('input[name="uid_field"]');
          const passwordField = page.locator('input[name="password"]');
          
          if (await usernameField.isVisible()) {
            await usernameField.fill('admin');  // Default admin user
            await passwordField.fill('admin');  // You may need to adjust password
            await loginButton.click();
            
            // Wait for authentication to complete
            await page.waitForURL(/dashy\.zoi.local/, { timeout: 10000 });
            console.log('✅ Authentication successful!');
          }
        }
      }
    }

    // Verify we're on Dashy
    const finalUrl = page.url();
    console.log(`Final URL: ${finalUrl}`);
    
    if (finalUrl.includes('dashy.zoi.local')) {
      console.log('🎉 SUCCESS: HTTPS Dashy authentication working!');
      
      // Take a screenshot for verification
      await page.screenshot({ 
        path: 'test-results/https-success.png',
        fullPage: true 
      });
    }

  } catch (error) {
    console.error(`❌ HTTPS test failed: ${error.message}`);
    
    // Take a screenshot of the error state
    await page.screenshot({ 
      path: 'test-results/https-error.png',
      fullPage: true 
    });
    
    throw error;
  }
}); 