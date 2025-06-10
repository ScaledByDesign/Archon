const { test, expect } = require('@playwright/test');

test('verify authentication flow and Dashy access', async ({ page }) => {
  console.log('🔍 Verifying complete authentication flow...');
  
  await page.setViewportSize({ width: 1280, height: 720 });
  
  try {
    // Step 1: Navigate to Dashy
    console.log('1️⃣ Going to Dashy...');
    await page.goto('https://dashy.localhost', { waitUntil: 'networkidle' });
    
    let currentUrl = page.url();
    console.log(`Initial URL: ${currentUrl}`);
    
    // Step 2: If we're redirected to auth, complete the login
    if (currentUrl.includes(':9000') || currentUrl.includes('auth')) {
      console.log('2️⃣ Detected auth redirect - performing login...');
      
      // Wait for login form
      await page.waitForSelector('input[name="uidField"]', { timeout: 10000 });
      
      // Fill and submit credentials
      await page.fill('input[name="uidField"]', 'admin@localhost');
      await page.fill('input[name="password"]', 'change-me-authentik-admin');
      
      console.log('3️⃣ Submitting login form...');
      await page.click('button[type="submit"]');
      
      // Wait for form submission to process
      await page.waitForTimeout(3000);
      
      // Check what happened after submission
      currentUrl = page.url();
      console.log(`Post-submit URL: ${currentUrl}`);
      
      // Step 3: Try to force navigation to Dashy
      if (currentUrl.includes(':9000')) {
        console.log('4️⃣ Still on auth page - trying direct navigation...');
        
        // Try navigating directly
        await page.goto('https://dashy.localhost', { 
          waitUntil: 'networkidle',
          timeout: 10000 
        });
        
        currentUrl = page.url();
        console.log(`After direct navigation: ${currentUrl}`);
      }
    } else {
      console.log('2️⃣ No auth redirect - already authenticated or different issue');
    }
    
    // Step 4: Analyze final state
    console.log('5️⃣ Analyzing final state...');
    
    const finalUrl = page.url();
    const pageTitle = await page.title();
    const pageContent = await page.textContent('body').catch(() => 'Could not read body');
    
    console.log(`Final URL: ${finalUrl}`);
    console.log(`Page Title: ${pageTitle}`);
    console.log(`Page content preview: ${pageContent.substring(0, 200)}...`);
    
    // Check for Dashy-specific elements
    const isDashyPage = await page.locator('nav, .item, .logo, [class*="dashy"], [class*="dashboard"]').count() > 0;
    const hasAuthForm = await page.locator('input[name="uidField"], input[name="password"]').count() > 0;
    
    console.log(`Has Dashy elements: ${isDashyPage}`);
    console.log(`Has auth form: ${hasAuthForm}`);
    
    // Take comprehensive screenshot
    await page.screenshot({ path: 'auth-flow-verification.png', fullPage: true });
    
    // Step 5: Determine auth status
    if (finalUrl.includes('dashy.localhost') && !finalUrl.includes(':9000')) {
      if (isDashyPage) {
        console.log('🎉 SUCCESS: Authenticated and on Dashy page!');
      } else {
        console.log('⚠️ PARTIAL: On Dashy domain but page content unclear');
      }
    } else if (hasAuthForm) {
      console.log('❌ FAILED: Still on authentication page');
    } else {
      console.log('🤔 UNCLEAR: Unexpected state - check screenshot');
    }
    
    // Step 6: Test specific Dashy functionality
    if (!hasAuthForm) {
      console.log('6️⃣ Testing Dashy functionality...');
      
      try {
        // Look for common Dashy elements
        const dashyElements = await page.locator('h1, .title, .search, .widget, .app-icon').count();
        console.log(`Found ${dashyElements} potential Dashy elements`);
        
        if (dashyElements > 0) {
          console.log('✅ Dashy elements detected - authentication successful!');
        } else {
          console.log('⚠️ No Dashy elements found - may need configuration');
        }
      } catch (error) {
        console.log(`Error testing Dashy functionality: ${error.message}`);
      }
    }
    
  } catch (error) {
    console.error('💥 Verification failed:', error.message);
    await page.screenshot({ path: 'verification-error.png', fullPage: true });
    throw error;
  }
});

test('test manual URL navigation after auth', async ({ page }) => {
  console.log('🧪 Testing manual URL patterns...');
  
  const urlsToTest = [
    'https://dashy.localhost',
    'https://dashy.localhost/',
    'http://dashy.localhost',
    'https://localhost:4001'  // Direct Dashy port
  ];
  
  for (const url of urlsToTest) {
    console.log(`Testing URL: ${url}`);
    
    try {
      await page.goto(url, { timeout: 10000, waitUntil: 'networkidle' });
      const finalUrl = page.url();
      const title = await page.title();
      
      console.log(`  Final URL: ${finalUrl}`);
      console.log(`  Title: ${title}`);
      
      const isAuthPage = finalUrl.includes(':9000') || finalUrl.includes('auth');
      const isDashyPage = finalUrl.includes('dashy') || finalUrl.includes('4001');
      
      console.log(`  Auth page: ${isAuthPage}, Dashy page: ${isDashyPage}`);
      
    } catch (error) {
      console.log(`  Error: ${error.message}`);
    }
    
    console.log('---');
  }
}); 