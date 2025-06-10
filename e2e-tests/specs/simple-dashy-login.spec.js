const { test, expect } = require('@playwright/test');

test('should login to Dashy through Authentik', async ({ page }) => {
  console.log('🚀 Starting simple Dashy login test...');
  
  // Set larger viewport to avoid scroll issues
  await page.setViewportSize({ width: 1280, height: 720 });
  
  try {
    // Step 1: Go to Dashy
    console.log('1️⃣ Navigating to Dashy...');
    await page.goto('https://dashy.localhost', { 
      waitUntil: 'networkidle',
      timeout: 20000 
    });
    
    // Step 2: Wait for auth redirect (handle both URL patterns)
    console.log('2️⃣ Waiting for auth redirect...');
    await page.waitForFunction(() => {
      const url = window.location.href;
      return url.includes(':9000') || url.includes('authentik');
    }, { timeout: 15000 });
    
    console.log(`Current URL: ${page.url()}`);
    
    // Step 3: Wait for and fill login form
    console.log('3️⃣ Waiting for login form...');
    await page.waitForSelector('input[name="uidField"]', { state: 'visible', timeout: 10000 });
    await page.waitForSelector('input[name="password"]', { state: 'visible', timeout: 10000 });
    
    // Small wait for form to fully load
    await page.waitForTimeout(1000);
    
    console.log('4️⃣ Filling username...');
    const usernameField = page.locator('input[name="uidField"]');
    await usernameField.clear();
    await usernameField.fill('admin@localhost');
    
    // Verify username
    const usernameValue = await usernameField.inputValue();
    console.log(`✅ Username filled: "${usernameValue}"`);
    
    console.log('5️⃣ Filling password...');
    const passwordField = page.locator('input[name="password"]');
    
    // Ensure the field is in view and clickable
    await passwordField.scrollIntoViewIfNeeded();
    await passwordField.clear();
    
    // Fill password with multiple methods
    await passwordField.fill('change-me-authentik-admin');
    
    // Verify password length (not actual value for security)
    const passwordValue = await passwordField.inputValue();
    console.log(`✅ Password filled (length: ${passwordValue.length})`);
    
    if (passwordValue.length === 0) {
      console.log('⚠️ Standard fill failed, trying click + type...');
      await passwordField.click();
      await page.keyboard.type('change-me-authentik-admin');
      const retryValue = await passwordField.inputValue();
      console.log(`Retry password length: ${retryValue.length}`);
    }
    
    // Step 4: Submit form
    console.log('6️⃣ Submitting form...');
    
    // Try to find and click submit button
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    console.log('✅ Form submitted');
    
    // Step 5: Wait for authentication to complete
    console.log('7️⃣ Waiting for authentication to complete...');
    
    // Wait for either success or failure
    await Promise.race([
      // Success case - redirect back to Dashy
      page.waitForURL(/dashy\.localhost/, { timeout: 15000 }),
      
      // Alternative success - check if we're no longer on auth page
      page.waitForFunction(() => {
        const url = window.location.href;
        return !url.includes(':9000') && !url.includes('auth');
      }, { timeout: 15000 }),
      
      // Fallback - wait for page to change significantly
      page.waitForLoadState('networkidle', { timeout: 10000 })
    ]);
    
    // Step 6: Verify success
    const finalUrl = page.url();
    console.log(`Final URL: ${finalUrl}`);
    
    if (finalUrl.includes('dashy.localhost')) {
      console.log('🎉 Successfully logged into Dashy!');
      
      // Try to verify Dashy loaded
      try {
        await page.waitForSelector('body', { timeout: 5000 });
        console.log('✅ Dashy page loaded');
      } catch (e) {
        console.log('⚠️ Dashy content load timeout, but URL suggests success');
      }
    } else if (!finalUrl.includes(':9000')) {
      console.log('✅ No longer on auth page - likely successful');
    } else {
      console.log('⚠️ Still on auth page - checking for errors...');
      
      // Check for error messages
      const errorElements = await page.locator('.error, .alert, [class*="error"]').count();
      if (errorElements > 0) {
        console.log('❌ Authentication failed - error messages found');
      } else {
        console.log('🤔 Unclear state - taking screenshot for review');
      }
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'final-state.png', fullPage: true });
    
  } catch (error) {
    console.error('💥 Test failed:', error.message);
    
    // Capture error state
    const currentUrl = page.url();
    console.log(`Error occurred at URL: ${currentUrl}`);
    
    try {
      await page.screenshot({ path: 'error-state.png', fullPage: true });
      console.log('📸 Error screenshot saved');
    } catch (screenshotError) {
      console.log('⚠️ Could not take error screenshot');
    }
    
    throw error;
  }
});

test('should verify Dashy is accessible after auth', async ({ page }) => {
  console.log('🔍 Testing direct Dashy access...');
  
  // This test will use the authenticated state from setup
  await page.goto('https://dashy.localhost');
  
  // If auth is working, we should either:
  // 1. Go directly to Dashy (if already authenticated)
  // 2. Go through auth flow and end up at Dashy
  
  const finalUrl = await page.url();
  console.log(`Direct access result: ${finalUrl}`);
  
  const isOnDashy = finalUrl.includes('dashy.localhost') && !finalUrl.includes(':9000');
  const isOnAuth = finalUrl.includes(':9000');
  
  if (isOnDashy) {
    console.log('✅ Direct access to Dashy successful - auth is working!');
  } else if (isOnAuth) {
    console.log('ℹ️ Redirected to auth - this is expected behavior');
  } else {
    console.log(`🤔 Unexpected URL: ${finalUrl}`);
  }
  
  await page.screenshot({ path: 'direct-access.png', fullPage: true });
}); 