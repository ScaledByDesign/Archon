const { test, expect } = require('@playwright/test');

test.describe('Authentik Robust Authentication', () => {
  test('should successfully authenticate through Authentik forward auth', async ({ page }) => {
    // Configure page for better reliability
    await page.setDefaultTimeout(30000);
    
    console.log('🚀 Starting robust Authentik authentication test...');
    
    try {
      // Step 1: Navigate to protected resource
      console.log('1️⃣ Navigating to protected resource...');
      await page.goto('https://dashy.localhost', { 
        waitUntil: 'networkidle',
        timeout: 20000 
      });
      
      // Step 2: Wait for redirect to authentication
      console.log('2️⃣ Waiting for authentication redirect...');
      await page.waitForFunction(() => {
        return window.location.href.includes('localhost:9000') || 
               window.location.href.includes('authentik');
      }, { timeout: 15000 });
      
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);
      
      // Step 3: Wait for login form to be ready
      console.log('3️⃣ Waiting for login form to be fully loaded...');
      
      // Use multiple strategies to ensure form is ready
      await Promise.all([
        page.waitForSelector('input[name="uidField"]', { state: 'visible' }),
        page.waitForSelector('input[name="password"]', { state: 'visible' }),
        page.waitForLoadState('networkidle')
      ]);
      
      // Additional wait for SPA to fully initialize
      await page.waitForTimeout(2000);
      
      // Step 4: Advanced form filling with multiple strategies
      console.log('4️⃣ Filling authentication form with robust method...');
      
      const credentials = {
        username: 'admin@localhost',
        password: 'change-me-authentik-admin'
      };
      
      // Username field - multiple strategies
      const usernameField = 'input[name="uidField"]';
      await page.waitForSelector(usernameField, { state: 'visible' });
      await page.click(usernameField); // Focus first
      await page.fill(usernameField, ''); // Clear any existing value
      await page.type(usernameField, credentials.username, { delay: 50 }); // Type with delay
      
      // Verify username was entered
      const usernameValue = await page.inputValue(usernameField);
      console.log(`✅ Username entered: "${usernameValue}"`);
      
      // Password field - enhanced strategy for SPA reactivity
      const passwordField = 'input[name="password"]';
      await page.waitForSelector(passwordField, { state: 'visible' });
      
      // Focus and wait for field to be fully interactive
      await page.click(passwordField);
      await page.waitForTimeout(500); // Allow for any dynamic behavior
      
      // Clear and fill password using multiple methods
      await page.fill(passwordField, '');
      await page.waitForTimeout(100);
      
      // Method 1: Standard fill
      await page.fill(passwordField, credentials.password);
      
      let passwordValue = await page.inputValue(passwordField);
      
      // Method 2: If fill didn't work, try typing
      if (passwordValue.length === 0) {
        console.log('⚠️ Standard fill failed, trying typing method...');
        await page.type(passwordField, credentials.password, { delay: 50 });
        passwordValue = await page.inputValue(passwordField);
      }
      
      // Method 3: If still empty, try direct JavaScript
      if (passwordValue.length === 0) {
        console.log('⚠️ Typing failed, trying JavaScript injection...');
        await page.evaluate((field, value) => {
          const element = document.querySelector(field);
          if (element) {
            element.value = value;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('blur', { bubbles: true }));
          }
        }, passwordField, credentials.password);
        passwordValue = await page.inputValue(passwordField);
      }
      
      console.log(`✅ Password field value length: ${passwordValue.length}`);
      
      if (passwordValue.length === 0) {
        throw new Error('❌ Failed to fill password field with all methods');
      }
      
      // Take screenshot before submission for debugging
      await page.screenshot({ path: 'before-submit.png', fullPage: true });
      
      // Step 5: Submit form with enhanced error handling
      console.log('5️⃣ Submitting authentication form...');
      
      // Try multiple submit strategies
      const submitStrategies = [
        async () => {
          await page.click('button[type="submit"]');
        },
        async () => {
          await page.press(passwordField, 'Enter');
        },
        async () => {
          await page.click('button:has-text("Sign in")');
        },
        async () => {
          await page.click('input[type="submit"]');
        }
      ];
      
      let submitted = false;
      for (const strategy of submitStrategies) {
        try {
          await strategy();
          console.log('✅ Form submitted');
          submitted = true;
          break;
        } catch (e) {
          console.log(`⚠️ Submit strategy failed: ${e.message}`);
        }
      }
      
      if (!submitted) {
        throw new Error('❌ Failed to submit form with all strategies');
      }
      
      // Step 6: Wait for authentication completion with robust checks
      console.log('6️⃣ Waiting for authentication completion...');
      
      // Wait for one of several possible success conditions
      await Promise.race([
        // Success: Redirect to original destination
        page.waitForURL('https://dashy.localhost/**', { timeout: 20000 }),
        
        // Success: URL contains dashy domain
        page.waitForFunction(() => {
          return window.location.hostname === 'dashy.localhost';
        }, { timeout: 20000 }),
        
        // Alternative: Look for authentication success indicators
        page.waitForSelector('[data-testid="authenticated"]', { timeout: 10000 }).catch(() => null),
        
        // Fallback: Check for absence of login form
        page.waitForFunction(() => {
          return !document.querySelector('input[name="uidField"]');
        }, { timeout: 15000 })
      ]);
      
      // Step 7: Verify successful authentication
      console.log('7️⃣ Verifying authentication success...');
      
      const finalUrl = page.url();
      console.log(`Final URL: ${finalUrl}`);
      
      // Take final screenshot
      await page.screenshot({ path: 'after-auth.png', fullPage: true });
      
      // Check for successful authentication indicators
      const isAuthenticated = finalUrl.includes('dashy.localhost') || 
                             finalUrl.includes('dashboard') ||
                             await page.locator('input[name="uidField"]').count() === 0;
      
      if (isAuthenticated) {
        console.log('🎉 Authentication successful!');
        
        // Additional verification - try to access page content
        try {
          await page.waitForSelector('body', { timeout: 5000 });
          console.log('✅ Page content loaded successfully');
        } catch (e) {
          console.log('⚠️ Page content loading timeout, but authentication appears successful');
        }
      } else {
        throw new Error('❌ Authentication verification failed');
      }
      
    } catch (error) {
      console.error('💥 Test failed:', error.message);
      
      // Take error screenshot for debugging
      await page.screenshot({ path: 'test-error.png', fullPage: true });
      
      // Log current page state for debugging
      const currentUrl = page.url();
      const title = await page.title();
      console.log(`Error state - URL: ${currentUrl}, Title: ${title}`);
      
      throw error;
    }
  });
  
  test('should handle authentication errors gracefully', async ({ page }) => {
    console.log('🧪 Testing authentication error handling...');
    
    await page.goto('https://dashy.localhost');
    
    // Wait for auth redirect
    await page.waitForFunction(() => {
      return window.location.href.includes('localhost:9000');
    }, { timeout: 15000 });
    
    // Try with wrong credentials
    await page.waitForSelector('input[name="uidField"]');
    await page.fill('input[name="uidField"]', 'wrong@user.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    
    await page.click('button[type="submit"]');
    
    // Should see error message or stay on login page
    await page.waitForTimeout(3000);
    
    const currentUrl = page.url();
    const hasErrorMessage = await page.locator('.error, .alert, [class*="error"]').count() > 0;
    const stillOnLogin = currentUrl.includes('localhost:9000');
    
    expect(stillOnLogin || hasErrorMessage).toBeTruthy();
    console.log('✅ Error handling verified');
  });
}); 