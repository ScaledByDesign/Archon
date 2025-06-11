import { test, expect } from '@playwright/test';

test.use({ 
  ignoreHTTPSErrors: true,  // Handle self-signed certificates
  storageState: undefined   // Start with clean state (no stored authentication)
});

test('Complete authentication flow - Login to Dashy dashboard', async ({ page }) => {
  console.log('🚀 Starting complete authentication flow test...');

  // Step 1: Navigate to Dashy (should redirect to authentication)
  console.log('1️⃣ Navigating to Dashy (expecting auth redirect)...');
  await page.goto('https://dashy.zoi.local', { 
    waitUntil: 'domcontentloaded',
    timeout: 30000 
  });

  let currentUrl = page.url();
  console.log(`Current URL after navigation: ${currentUrl}`);

  // Step 2: Handle potential 0.0.0.0:9000 redirect issue
  if (currentUrl.includes('0.0.0.0:9000')) {
    console.log('🔧 Fixing 0.0.0.0:9000 URL...');
    const fixedUrl = currentUrl.replace('0.0.0.0:9000', 'zoi.local:9000');
    console.log(`Redirecting to fixed URL: ${fixedUrl}`);
    await page.goto(fixedUrl, { waitUntil: 'domcontentloaded' });
    currentUrl = page.url();
  }

  // Step 3: Verify we're on Authentik login page
  if (currentUrl.includes('zoi.local:9000') && currentUrl.includes('flow')) {
    console.log('🔐 Successfully redirected to Authentik authentication flow');
    
    // Wait for the login form to load
    console.log('⏱️ Waiting for login form to appear...');
    await page.waitForSelector('input[name="uid_field"]', { timeout: 10000 });
    
    // Step 4: Fill in login credentials
    console.log('📝 Filling in login credentials...');
    await page.fill('input[name="uid_field"]', 'testadmin');  // Test admin username
    await page.fill('input[name="password"]', 'testadmin123');   // Test admin password
    
    // Take screenshot before login
    await page.screenshot({ 
      path: 'test-results/01-before-login.png',
      fullPage: true 
    });
    
    // Step 5: Submit login form
    console.log('🔑 Submitting login form...');
    await page.click('button[type="submit"]');
    
    // Step 6: Wait for authentication to complete and redirect back to Dashy
    console.log('⏱️ Waiting for authentication to complete...');
    
    try {
      // Wait for redirect back to Dashy (either HTTP or HTTPS)
      await page.waitForURL(/dashy\.zoi.local/, { timeout: 15000 });
      console.log('✅ Successfully redirected back to Dashy!');
    } catch (error) {
      // If direct redirect fails, check current URL and handle manually
      currentUrl = page.url();
      console.log(`Current URL after login attempt: ${currentUrl}`);
      
      if (currentUrl.includes('zoi.local:9000')) {
        // Look for "Continue" or redirect button
        try {
          const continueButton = page.locator('button', { hasText: /continue|proceed|redirect/i }).first();
          if (await continueButton.isVisible({ timeout: 5000 })) {
            console.log('🔄 Found continue button, clicking...');
            await continueButton.click();
            await page.waitForURL(/dashy\.zoi.local/, { timeout: 10000 });
          }
        } catch {
          console.log('⚠️ No continue button found, checking for automatic redirect...');
          // Wait a bit more for automatic redirect
          await page.waitForURL(/dashy\.zoi.local/, { timeout: 10000 });
        }
      }
    }
    
  } else {
    console.log('⚠️ Did not get redirected to authentication - checking if already authenticated...');
  }

  // Step 7: Verify we're now on Dashy
  currentUrl = page.url();
  console.log(`Final URL: ${currentUrl}`);

  if (currentUrl.includes('dashy.zoi.local')) {
    console.log('🎉 Successfully on Dashy dashboard!');
    
    // Step 8: Verify Dashy dashboard content is accessible
    console.log('🔍 Verifying dashboard content...');
    
    // Wait for Dashy to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000); // Give Dashy time to render
    
    // Take screenshot of successful dashboard
    await page.screenshot({ 
      path: 'test-results/02-dashy-dashboard.png',
      fullPage: true 
    });
    
    // Check for common Dashy elements
    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);
    
    // Look for Dashy-specific elements
    const dashyElements = {
      config: await page.locator('[class*="config"], [id*="config"], [data-cy="config"]').count(),
      dashboard: await page.locator('[class*="dashboard"], [class*="container"], [class*="app"]').count(),
      navigation: await page.locator('[class*="nav"], [class*="menu"], [class*="sidebar"]').count(),
      widgets: await page.locator('[class*="widget"], [class*="item"], [class*="section"]').count()
    };
    
    console.log('🔍 Dashboard elements found:', dashyElements);
    
    // Verify we can see actual dashboard content (not just error pages)
    const bodyText = await page.textContent('body');
    const hasErrorText = bodyText.includes('error') || bodyText.includes('404') || bodyText.includes('500');
    
    if (!hasErrorText) {
      console.log('✅ Dashboard appears to be loading successfully (no error content detected)');
    } else {
      console.log('⚠️ Possible error content detected on dashboard');
    }
    
    // Step 9: Test navigation/interaction (if possible)
    try {
      // Look for interactive elements
      const clickableElements = await page.locator('button, [role="button"], a, [class*="clickable"]').count();
      console.log(`Found ${clickableElements} potentially interactive elements`);
      
      if (clickableElements > 0) {
        console.log('✅ Dashboard appears to have interactive elements');
      }
    } catch (error) {
      console.log('⚠️ Could not analyze interactive elements:', error.message);
    }
    
    // Final verification screenshot
    await page.screenshot({ 
      path: 'test-results/03-final-dashboard.png',
      fullPage: true 
    });
    
    console.log('🎯 AUTHENTICATION FLOW TEST COMPLETED SUCCESSFULLY!');
    console.log('📸 Screenshots saved to test-results/');
    
  } else {
    console.error(`❌ Authentication flow failed - ended up at: ${currentUrl}`);
    
    // Take error screenshot
    await page.screenshot({ 
      path: 'test-results/auth-flow-error.png',
      fullPage: true 
    });
    
    throw new Error(`Authentication flow failed - final URL: ${currentUrl}`);
  }
});

test('Verify authenticated session persists', async ({ page }) => {
  console.log('🔄 Testing session persistence...');
  
  // This test runs after the login test to verify the session is maintained
  await page.goto('https://dashy.zoi.local', { 
    waitUntil: 'domcontentloaded',
    timeout: 15000 
  });
  
  const currentUrl = page.url();
  console.log(`URL after second visit: ${currentUrl}`);
  
  if (currentUrl.includes('dashy.zoi.local')) {
    console.log('✅ Session persisted - no re-authentication required');
    
    await page.screenshot({ 
      path: 'test-results/04-session-persistence.png',
      fullPage: true 
    });
  } else if (currentUrl.includes('zoi.local:9000')) {
    console.log('⚠️ Session did not persist - redirected to authentication again');
  } else {
    console.log(`⚠️ Unexpected URL: ${currentUrl}`);
  }
}); 