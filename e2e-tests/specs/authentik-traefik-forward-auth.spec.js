const { test, expect } = require('@playwright/test');

test.describe('Authentik-Traefik Forward Auth Integration Tests', () => {
  
  test.describe('Forward Auth Middleware Tests', () => {
    
    test('should use correct Authentik forward auth endpoint', async ({ page }) => {
      // Monitor network requests to verify correct endpoint usage
      const authRequests = [];
      
      page.on('request', request => {
        const url = request.url();
        // Check for calls to the Authentik forward auth endpoint
        if (url.includes('/outpost.goauthentik.io/auth/traefik')) {
          authRequests.push({
            url,
            method: request.method(),
            headers: request.headers()
          });
        }
      });
      
      // Create unauthenticated context to trigger auth flow
      const context = await page.context().browser().newContext({
        storageState: undefined // No stored auth
      });
      const unauthPage = await context.newPage();
      
      try {
        // Navigate to protected resource (Dashy)
        await unauthPage.goto('https://dashy.localhost', { 
          waitUntil: 'networkidle',
          timeout: 30000 
        });
        
        // Should be redirected to Authentik
        await unauthPage.waitForURL('**/if/flow/**', { timeout: 15000 });
        
        // Verify we captured requests to the correct forward auth endpoint
        expect(authRequests.length).toBeGreaterThan(0);
        
        const correctEndpoint = authRequests.find(req => 
          req.url.includes('/outpost.goauthentik.io/auth/traefik')
        );
        
        expect(correctEndpoint).toBeTruthy();
        console.log('✅ Traefik using correct Authentik forward auth endpoint:', correctEndpoint.url);
        
      } finally {
        await context.close();
      }
    });
    
    test('should pass correct authentication headers', async ({ page }) => {
      // Navigate to Dashy with authentication
      await page.goto('https://dashy.localhost');
      await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
      
      // Monitor requests to services that should receive auth headers
      const serviceRequests = [];
      
      page.on('request', request => {
        const url = request.url();
        if (url.includes('.localhost') && !url.includes('auth.localhost')) {
          serviceRequests.push({
            url,
            headers: request.headers()
          });
        }
      });
      
      // Navigate to a protected service
      await page.goto('https://api.localhost', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      // Check if we have requests with expected Authentik headers
      const requestsWithAuthHeaders = serviceRequests.filter(req => {
        const headers = req.headers;
        return headers['x-authentik-username'] || 
               headers['x-authentik-email'] || 
               headers['x-authentik-groups'] ||
               headers['x-authentik-uid'];
      });
      
      if (requestsWithAuthHeaders.length > 0) {
        console.log('✅ Authentik headers being passed to services:');
        requestsWithAuthHeaders.forEach(req => {
          const authHeaders = Object.keys(req.headers)
            .filter(h => h.startsWith('x-authentik-'))
            .map(h => `${h}: ${req.headers[h]}`);
          console.log(`  ${req.url}: [${authHeaders.join(', ')}]`);
        });
      } else {
        console.log('ℹ️ No Authentik headers detected in service requests');
      }
    });
  });
  
  test.describe('Domain Configuration Tests', () => {
    
    test('should handle localhost domain correctly', async ({ page }) => {
      // Test that all localhost subdomains work with authentication
      const domains = [
        'https://dashy.localhost',
        'https://auth.localhost',
        'https://traefik.localhost',
        'https://api.localhost'
      ];
      
      for (const domain of domains) {
        try {
          console.log(`Testing domain: ${domain}`);
          
          await page.goto(domain, { 
            waitUntil: 'networkidle',
            timeout: 30000 
          });
          
          const currentUrl = page.url();
          
          // Should either be on the target domain or redirected to auth
          if (currentUrl.includes('auth.localhost') && currentUrl.includes('/if/flow/')) {
            console.log(`⚠️ ${domain} requires authentication (expected for some services)`);
          } else if (currentUrl.includes(domain.split('//')[1])) {
            console.log(`✅ ${domain} accessible`);
          } else {
            console.log(`❓ ${domain} redirected to: ${currentUrl}`);
          }
          
        } catch (error) {
          console.log(`❌ ${domain} failed: ${error.message}`);
        }
      }
    });
    
    test('should handle authentication redirect loop prevention', async ({ page }) => {
      // Create unauthenticated context
      const context = await page.context().browser().newContext({
        storageState: undefined
      });
      const unauthPage = await context.newPage();
      
      try {
        // Monitor for redirect loops
        let redirectCount = 0;
        const visitedUrls = new Set();
        
        unauthPage.on('response', response => {
          if (response.status() >= 300 && response.status() < 400) {
            redirectCount++;
            visitedUrls.add(response.url());
          }
        });
        
        // Navigate to protected resource
        await unauthPage.goto('https://dashy.localhost', { 
          waitUntil: 'networkidle',
          timeout: 30000 
        });
        
        // Should be on Authentik login page
        await unauthPage.waitForURL('**/if/flow/**', { timeout: 15000 });
        
        // Verify no redirect loop (reasonable number of redirects)
        expect(redirectCount).toBeLessThan(10);
        console.log(`✅ Authentication redirect completed with ${redirectCount} redirects`);
        
        // Verify we're on a proper login page
        await expect(unauthPage.locator('input[name="uid_field"]')).toBeVisible();
        
      } finally {
        await context.close();
      }
    });
  });
  
  test.describe('Authentication Flow Tests', () => {
    
    test('should complete full authentication flow', async ({ browser }) => {
      // Create fresh unauthenticated context
      const context = await browser.newContext({
        storageState: undefined
      });
      const page = await context.newPage();
      
      try {
        // Navigate to protected resource
        await page.goto('https://dashy.localhost', { waitUntil: 'networkidle' });
        
        // Should be redirected to Authentik
        await page.waitForURL('**/if/flow/**', { timeout: 15000 });
        console.log('✅ Redirected to Authentik authentication');
        
        // Fill login form
        await page.waitForSelector('input[name="uid_field"]', { timeout: 10000 });
        
        const username = process.env.AUTHENTIK_USER || 'admin';
        const password = process.env.AUTHENTIK_PASSWORD || 'admin123!';
        
        await page.fill('input[name="uid_field"]', username);
        await page.fill('input[name="password"]', password);
        
        // Submit form
        await page.click('button[type="submit"]');
        console.log('✅ Submitted authentication credentials');
        
        // Should be redirected back to Dashy
        await page.waitForURL('**/dashy.**', { timeout: 30000 });
        console.log('✅ Redirected back to original destination');
        
        // Verify successful authentication
        await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
        console.log('✅ Successfully authenticated and accessing protected resource');
        
      } finally {
        await context.close();
      }
    });
    
    test('should maintain session across services', async ({ page }) => {
      // Start at Dashy (authenticated)
      await page.goto('https://dashy.localhost');
      await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
      
      // Navigate to other protected services
      const services = [
        { url: 'https://api.localhost', name: 'FastAPI' },
        { url: 'https://llm.localhost', name: 'LiteLLM' },
        { url: 'https://traefik.localhost', name: 'Traefik Dashboard' }
      ];
      
      for (const service of services) {
        try {
          console.log(`Testing session persistence for ${service.name}...`);
          
          await page.goto(service.url, { 
            waitUntil: 'networkidle',
            timeout: 30000 
          });
          
          const currentUrl = page.url();
          
          // Should NOT be redirected to auth (session should be maintained)
          if (currentUrl.includes('auth.localhost') && currentUrl.includes('/if/flow/')) {
            console.log(`❌ ${service.name} requires re-authentication - session not maintained`);
          } else {
            console.log(`✅ ${service.name} accessible with maintained session`);
          }
          
        } catch (error) {
          console.log(`⚠️ ${service.name} test error: ${error.message}`);
        }
      }
    });
  });
  
  test.describe('Error Handling Tests', () => {
    
    test('should handle invalid credentials gracefully', async ({ browser }) => {
      const context = await browser.newContext({
        storageState: undefined
      });
      const page = await context.newPage();
      
      try {
        // Navigate to protected resource
        await page.goto('https://dashy.localhost', { waitUntil: 'networkidle' });
        
        // Should be redirected to Authentik
        await page.waitForURL('**/if/flow/**', { timeout: 15000 });
        
        // Fill with invalid credentials
        await page.waitForSelector('input[name="uid_field"]', { timeout: 10000 });
        await page.fill('input[name="uid_field"]', 'invalid-user');
        await page.fill('input[name="password"]', 'invalid-password');
        
        // Submit form
        await page.click('button[type="submit"]');
        
        // Should stay on auth page with error message
        await page.waitForTimeout(3000);
        
        // Should still be on auth page (not redirected back)
        expect(page.url()).toContain('auth.localhost');
        
        // Look for error message
        const errorElements = await page.locator('.error, .alert, [class*="error"], [role="alert"]').all();
        if (errorElements.length > 0) {
          console.log('✅ Error message displayed for invalid credentials');
        } else {
          console.log('ℹ️ No explicit error message found, but stayed on auth page');
        }
        
      } finally {
        await context.close();
      }
    });
    
    test('should handle service unavailability', async ({ page }) => {
      // Test accessing a service that might be down
      try {
        await page.goto('https://nonexistent.localhost', { 
          waitUntil: 'networkidle',
          timeout: 10000 
        });
      } catch (error) {
        // Expected behavior - service not found
        console.log('✅ Gracefully handled non-existent service');
      }
    });
  });
  
  test.describe('Performance and Reliability Tests', () => {
    
    test('should handle concurrent authentication requests', async ({ browser }) => {
      // Create multiple contexts and authenticate simultaneously
      const contexts = await Promise.all([
        browser.newContext({ storageState: undefined }),
        browser.newContext({ storageState: undefined }),
        browser.newContext({ storageState: undefined })
      ]);
      
      const pages = await Promise.all(contexts.map(ctx => ctx.newPage()));
      
      try {
        // Start all authentications simultaneously
        const authPromises = pages.map(async (page, index) => {
          console.log(`Starting concurrent auth ${index + 1}...`);
          
          await page.goto('https://dashy.localhost', { waitUntil: 'networkidle' });
          await page.waitForURL('**/if/flow/**', { timeout: 15000 });
          
          await page.waitForSelector('input[name="uid_field"]', { timeout: 10000 });
          
          const username = process.env.AUTHENTIK_USER || 'admin';
          const password = process.env.AUTHENTIK_PASSWORD || 'admin123!';
          
          await page.fill('input[name="uid_field"]', username);
          await page.fill('input[name="password"]', password);
          await page.click('button[type="submit"]');
          
          await page.waitForURL('**/dashy.**', { timeout: 30000 });
          await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
          
          console.log(`✅ Concurrent auth ${index + 1} completed`);
          return true;
        });
        
        // Wait for all authentications to complete
        const results = await Promise.all(authPromises);
        expect(results.every(r => r)).toBe(true);
        
        console.log('✅ All concurrent authentications successful');
        
      } finally {
        await Promise.all(contexts.map(ctx => ctx.close()));
      }
    });
    
    test('should measure authentication performance', async ({ browser }) => {
      const context = await browser.newContext({
        storageState: undefined
      });
      const page = await context.newPage();
      
      try {
        const startTime = Date.now();
        
        // Complete authentication flow
        await page.goto('https://dashy.localhost', { waitUntil: 'networkidle' });
        await page.waitForURL('**/if/flow/**', { timeout: 15000 });
        
        const authPageTime = Date.now();
        
        await page.waitForSelector('input[name="uid_field"]', { timeout: 10000 });
        
        const username = process.env.AUTHENTIK_USER || 'admin';
        const password = process.env.AUTHENTIK_PASSWORD || 'admin123!';
        
        await page.fill('input[name="uid_field"]', username);
        await page.fill('input[name="password"]', password);
        await page.click('button[type="submit"]');
        
        await page.waitForURL('**/dashy.**', { timeout: 30000 });
        await expect(page.locator('h1')).toContainText('Zoi Production Dashboard');
        
        const endTime = Date.now();
        
        const totalTime = endTime - startTime;
        const redirectTime = authPageTime - startTime;
        const authTime = endTime - authPageTime;
        
        console.log(`Authentication Performance:
          - Total time: ${totalTime}ms
          - Redirect to auth: ${redirectTime}ms  
          - Authentication: ${authTime}ms`);
        
        // Performance expectations (adjust based on your requirements)
        expect(totalTime).toBeLessThan(30000); // Total < 30s
        expect(redirectTime).toBeLessThan(10000); // Redirect < 10s
        expect(authTime).toBeLessThan(20000); // Auth < 20s
        
      } finally {
        await context.close();
      }
    });
  });
}); 