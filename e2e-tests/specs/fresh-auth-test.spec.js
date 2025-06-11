import { test, expect } from '@playwright/test';

test.use({ 
  ignoreHTTPSErrors: true,
  storageState: undefined  // Start completely fresh
});

test('Fresh authentication flow - Test callback handling', async ({ page }) => {
  console.log('🆕 Starting fresh authentication test...');
  
  try {
    // Step 1: Navigate to Dashy (should redirect to auth)
    console.log('1️⃣ Navigating to Dashy...');
    await page.goto('https://dashy.zoi.local', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });

    let currentUrl = page.url();
    console.log(`URL after navigation: ${currentUrl}`);

    // Step 2: Handle 0.0.0.0:9000 URL fix if needed
    if (currentUrl.includes('0.0.0.0:9000')) {
      console.log('🔧 Fixing 0.0.0.0:9000 URL...');
      const fixedUrl = currentUrl.replace('0.0.0.0:9000', 'zoi.local:9000');
      console.log(`Redirecting to: ${fixedUrl}`);
      await page.goto(fixedUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      currentUrl = page.url();
    }

    console.log(`Current URL: ${currentUrl}`);

    // Step 3: Wait for login form and fill it out
    console.log('3️⃣ Looking for login form...');
    
    // Try different possible selectors for login fields
    const usernameSelectors = [
      'input[name="uidField"]',     // Correct Authentik field name (camelCase)
      'input[name="uid_field"]',    // Alternative snake_case version
      'input[name="username"]', 
      'input[name="email"]',
      'input[type="text"]',
      'input[type="email"]'
    ];
    
    let usernameField = null;
    for (const selector of usernameSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        usernameField = selector;
        console.log(`✅ Found username field: ${selector}`);
        break;
      } catch (e) {
        console.log(`❌ Username field not found: ${selector}`);
      }
    }

    if (!usernameField) {
      console.log('❌ No username field found, checking page content...');
      const pageContent = await page.content();
      console.log('Page title:', await page.title());
      console.log('Page contains login:', pageContent.includes('login') || pageContent.includes('Login'));
      console.log('Page contains auth:', pageContent.includes('auth') || pageContent.includes('Auth'));
      throw new Error('No login form found');
    }

    // Step 4: Fill login form
    console.log('4️⃣ Filling login form...');
    await page.fill(usernameField, 'admin@zoi.local');  // Bootstrap email from authentik.env
    console.log('✅ Username filled');
    
    // Verify username was filled
    const usernameValue = await page.inputValue(usernameField);
    console.log(`Username field value: "${usernameValue}"`);
    
    const passwordSelectors = [
      '#ak-stage-password-input',      // Specific Authentik password field ID
      'input[name="password"]',
      'input[type="password"]'
    ];
    
    let passwordField = null;
    for (const selector of passwordSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: 2000 });
        passwordField = selector;
        console.log(`✅ Found password field: ${selector}`);
        break;
      } catch (e) {
        console.log(`❌ Password field not found: ${selector}`);
      }
    }
    
    if (passwordField) {
      // Debug password field properties first
      console.log('🔍 Debugging password field...');
      const isVisible = await page.isVisible(passwordField);
      const isEnabled = await page.isEnabled(passwordField);
      const isEditable = await page.isEditable(passwordField);
      console.log(`Password field - Visible: ${isVisible}, Enabled: ${isEnabled}, Editable: ${isEditable}`);
      
      // Clear field first
      await page.fill(passwordField, '');
      console.log('🧹 Cleared password field');
      
      // Try multiple methods to fill the password
      const password = 'change-me-authentik-admin';
      
      // Method 1: Standard fill
      await page.fill(passwordField, password);
      let passwordValue = await page.inputValue(passwordField);
      console.log(`Method 1 (fill) - Password length: ${passwordValue.length}`);
      
      if (passwordValue.length === 0) {
        console.log('⚠️ Standard fill failed, trying click and type...');
        
        // Method 2: Click and type
        await page.click(passwordField);
        await page.type(passwordField, password);
        passwordValue = await page.inputValue(passwordField);
        console.log(`Method 2 (click+type) - Password length: ${passwordValue.length}`);
      }
      
             if (passwordValue.length === 0) {
         console.log('⚠️ Click+type failed, trying evaluate...');
         
         // Method 3: Direct JavaScript evaluation with more events
         await page.evaluate((selector, value) => {
           const element = document.querySelector(selector);
           if (element) {
             // Clear first
             element.value = '';
             element.focus();
             
             // Set value and trigger all possible events
             element.value = value;
             
             // Trigger events that might be needed
             element.dispatchEvent(new Event('focus', { bubbles: true }));
             element.dispatchEvent(new Event('input', { bubbles: true }));
             element.dispatchEvent(new Event('change', { bubbles: true }));
             element.dispatchEvent(new Event('keyup', { bubbles: true }));
             element.dispatchEvent(new Event('blur', { bubbles: true }));
           }
         }, passwordField, password);
         passwordValue = await page.inputValue(passwordField);
         console.log(`Method 3 (evaluate) - Password length: ${passwordValue.length}`);
       }
       
       if (passwordValue.length === 0) {
         console.log('⚠️ Evaluate failed, trying character-by-character typing...');
         
         // Method 4: Character by character with delays
         await page.click(passwordField);
         await page.keyboard.press('Control+a'); // Select all
         await page.keyboard.press('Delete'); // Delete
         
         for (const char of password) {
           await page.keyboard.type(char);
           await page.waitForTimeout(50); // Small delay between chars
         }
         
         passwordValue = await page.inputValue(passwordField);
         console.log(`Method 4 (char-by-char) - Password length: ${passwordValue.length}`);
       }
      
             // Final verification with screenshot
       if (passwordValue.length > 0) {
         console.log('✅ Password field shows length > 0, but taking screenshot to verify...');
         
         // Take screenshot to see actual state
         await page.screenshot({ path: 'debug-before-submit.png', fullPage: true });
         console.log('📸 Screenshot saved as debug-before-submit.png');
         
         // Also check if password field actually shows dots/asterisks visually
         const isPasswordMasked = await page.evaluate((selector) => {
           const element = document.querySelector(selector);
           if (element && element.type === 'password') {
             // Check if the field visually appears to have content
             return {
               value: element.value,
               valueLength: element.value.length,
               displayValue: element.value.replace(/./g, '*'), // Mask for logging
               hasContent: element.value.length > 0,
               isFocused: document.activeElement === element
             };
           }
           return null;
         }, passwordField);
         console.log('🔍 Password field visual state:', isPasswordMasked);
         
         // Try clicking the field and checking focus
         await page.click(passwordField);
         await page.waitForTimeout(500); // Brief pause
         const isFocused = await page.evaluate((selector) => {
           const element = document.querySelector(selector);
           return document.activeElement === element;
         }, passwordField);
         console.log(`🎯 Password field focused: ${isFocused}`);
         
       } else {
         console.log('❌ All password fill methods failed');
         
         // Get more info about the field
         const fieldInfo = await page.evaluate((selector) => {
           const element = document.querySelector(selector);
           if (element) {
             return {
               tagName: element.tagName,
               type: element.type,
               name: element.name,
               id: element.id,
               className: element.className,
               disabled: element.disabled,
               readOnly: element.readOnly,
               required: element.required
             };
           }
           return null;
         }, passwordField);
         console.log('Password field info:', fieldInfo);
       }
    } else {
      console.log('❌ No password field found');
    }

    // Step 5: Submit form and wait for navigation
    console.log('5️⃣ Submitting login form...');
    
    try {
      // Wait for navigation after clicking submit
      await Promise.all([
        page.waitForNavigation({ timeout: 15000 }),
        page.click('button[type="submit"]')
      ]);
      console.log('✅ Form submitted and navigation completed');
    } catch (error) {
      console.log('⚠️ Navigation wait failed, checking for errors...');
      
      // Check for authentication errors on the page
      const pageText = await page.textContent('body');
      if (pageText.includes('Invalid username') || pageText.includes('Invalid password') || pageText.includes('Invalid credentials')) {
        console.log('❌ Authentication failed - invalid credentials');
      } else if (pageText.includes('error') || pageText.includes('Error')) {
        console.log('❌ Authentication error detected:', pageText.substring(0, 200));
      }
      
      // Still wait a bit to see final state
      await page.waitForTimeout(3000);
    }

    // Step 6: Check result
    console.log('6️⃣ Checking authentication result...');
    
    const finalUrl = page.url();
    console.log(`Final URL: ${finalUrl}`);
    
    // Check if we successfully reached Dashy or got an error
    if (finalUrl.includes('/outpost.goauthentik.io/callback')) {
      console.log('⚠️ Stuck at callback URL - checking for errors');
      const pageText = await page.textContent('body');
      console.log('Callback page content:', pageText);
      
      if (pageText.includes('400') || pageText.includes('Bad Request')) {
        console.log('❌ 400 error confirmed at callback');
      }
    } else if (finalUrl.includes('dashy.zoi.local') && !finalUrl.includes('auth')) {
      console.log('✅ Successfully reached Dashy dashboard!');
      
      // Verify we can see dashboard content
      const dashyTitle = await page.title();
      console.log(`Dashy page title: ${dashyTitle}`);
      
      expect(finalUrl).toContain('dashy.zoi.local');
      expect(finalUrl).not.toContain('/outpost.goauthentik.io/callback');
    } else {
      console.log(`⚠️ Unexpected final URL: ${finalUrl}`);
    }
    
  } catch (error) {
    console.log(`❌ Test failed: ${error.message}`);
    const currentUrl = page.url();
    const title = await page.title();
    console.log(`Current URL: ${currentUrl}`);
    console.log(`Page title: ${title}`);
    throw error;
  }
}); 