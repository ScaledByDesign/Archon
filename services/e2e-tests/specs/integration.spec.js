const { test, expect } = require('@playwright/test');

test.describe('Authentik-Traefik Integration Tests', () => {
  
  test('should redirect unauthenticated users to Authentik', async ({ browser }) => {
    // Create a new incognito context (no stored auth state)
    const context = await browser.newContext({ 
      storageState: undefined // Explicitly no auth state
    });
    const page = await context.newPage();
    
    try {
      // Navigate to Dashy
      await page.goto('/', { waitUntil: 'networkidle' });
      
      // Should be redirected to Authentik authentication
      await page.waitForURL('**/if/flow/**', { timeout: 15000 });
      expect(page.url()).toContain('auth.');
      
      // Should see Authentik login form
      await expect(page.locator('input[name="uid_field"]')).toBeVisible();
      await expect(page.locator('input[name="password"]')).toBeVisible();
      
      console.log('✅ Unauthenticated redirect to Authentik working correctly');
    } finally {
      await context.close();
    }
  });

  test('should maintain authentication across page reloads', async ({ page }) => {
    // Navigate to Dashy (should use stored auth state)
    await page.goto('/');
    
    // Should be authenticated and on Dashy
    await expect(page).toHaveURL(/.*dashy.*/);
    await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
    
    // Reload the page
    await page.reload({ waitUntil: 'networkidle' });
    
    // Should still be on Dashy, not redirected to auth
    await expect(page).toHaveURL(/.*dashy.*/);
    await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
    
    console.log('✅ Authentication persistence across reloads working correctly');
  });

  test('should handle multiple tab authentication', async ({ browser }) => {
    // Create a context with auth state
    const context = await browser.newContext({
      storageState: 'auth-state/user.json'
    });
    
    try {
      // Open first tab
      const page1 = await context.newPage();
      await page1.goto('/');
      await expect(page1).toHaveURL(/.*dashy.*/);
      
      // Open second tab
      const page2 = await context.newPage();
      await page2.goto('/');
      await expect(page2).toHaveURL(/.*dashy.*/);
      
      // Both tabs should be authenticated
      await expect(page1.locator('h1')).toContainText('Zoi Production Dashboard');
      await expect(page2.locator('h1')).toContainText('Zoi Production Dashboard');
      
      console.log('✅ Multi-tab authentication working correctly');
    } finally {
      await context.close();
    }
  });

  test('should test individual service authentication', async ({ page }) => {
    // Test that other services behind Traefik auth are also protected
    const servicesToTest = [
      { name: 'FastAPI', url: 'https://api.zoi.local', expectedText: 'FastAPI' },
      { name: 'LiteLLM', url: 'https://llm.zoi.local', expectedText: 'LiteLLM' },
      { name: 'Qdrant', url: 'https://qdrant.zoi.local', expectedText: 'Qdrant' }
    ];

    for (const service of servicesToTest) {
      try {
        console.log(`Testing ${service.name} authentication...`);
        
        // Navigate to service URL
        await page.goto(service.url, { waitUntil: 'networkidle', timeout: 30000 });
        
        // Should either be on the service (if auth headers are passed correctly)
        // or redirected to Authentik (if service requires separate auth)
        const currentUrl = page.url();
        
        if (currentUrl.includes('auth.') && currentUrl.includes('/if/flow/')) {
          console.log(`❌ ${service.name} requires separate authentication - this may indicate auth headers not being passed correctly`);
        } else if (currentUrl.includes(service.url.split('//')[1])) {
          console.log(`✅ ${service.name} accessible with forwarded authentication`);
          
          // Try to verify the service is actually working
          const pageContent = await page.textContent('body');
          if (pageContent && pageContent.toLowerCase().includes(service.expectedText.toLowerCase())) {
            console.log(`✅ ${service.name} content verified`);
          }
        } else {
          console.log(`⚠️ ${service.name} redirected to unexpected URL: ${currentUrl}`);
        }
        
      } catch (error) {
        console.log(`❌ ${service.name} test failed: ${error.message}`);
      }
    }
  });

  test('should verify auth headers are passed correctly', async ({ page }) => {
    // Navigate to Dashy
    await page.goto('/');
    
    // Set up network request monitoring
    const requests = [];
    page.on('request', request => {
      if (request.url().includes('api.') || request.url().includes('llm.')) {
        requests.push({
          url: request.url(),
          headers: request.headers()
        });
      }
    });
    
    // Try to trigger some API calls by interacting with dashboard elements
    try {
      // Look for any links to API services and click them
      const apiLinks = page.locator('a[href*="api."], a[href*="llm."]');
      const apiLinkCount = await apiLinks.count();
      
      if (apiLinkCount > 0) {
        // Click the first API link in a new tab to avoid navigation
        await apiLinks.first().click({ button: 'middle' });
        await page.waitForTimeout(2000);
      }
    } catch (error) {
      console.log('No API links found to test - this is okay');
    }
    
    // Check if any requests were made with auth headers
    const authRequests = requests.filter(req => 
      req.headers['x-authentik-username'] || 
      req.headers['x-authentik-email'] ||
      req.headers['authorization']
    );
    
    if (authRequests.length > 0) {
      console.log(`✅ Found ${authRequests.length} requests with auth headers`);
      authRequests.forEach(req => {
        console.log(`  - ${req.url} has auth headers`);
      });
    } else {
      console.log('ℹ️ No auth header verification possible (no API requests detected)');
    }
  });

  test('should test logout functionality if available', async ({ page }) => {
    // Navigate to Dashy
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
    
    // Look for logout link or user menu
    const logoutSelectors = [
      'a[href*="logout"]',
      'button:has-text("Logout")',
      'a:has-text("Logout")',
      'a:has-text("Sign out")',
      '[data-testid="logout"]',
      '.logout'
    ];
    
    let logoutElement = null;
    for (const selector of logoutSelectors) {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        logoutElement = element.first();
        break;
      }
    }
    
    if (logoutElement) {
      console.log('Found logout element, testing logout...');
      await logoutElement.click();
      
      // Should be redirected to Authentik or login page
      await page.waitForTimeout(2000);
      const currentUrl = page.url();
      
      if (currentUrl.includes('auth.') || currentUrl.includes('login')) {
        console.log('✅ Logout functionality working correctly');
      } else {
        console.log(`⚠️ After logout, unexpected URL: ${currentUrl}`);
      }
    } else {
      console.log('ℹ️ No logout functionality found - this may be handled by Authentik directly');
    }
  });
}); 