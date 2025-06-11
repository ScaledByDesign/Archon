import { test as setup, expect } from '@playwright/test';

const authFile = './auth-state/user.json';

setup('authenticate with Authentik', async ({ page }) => {
  console.log('Starting authentication setup...');
  
  // Set a shorter timeout for initial navigation
  page.setDefaultTimeout(15000);
  
  // Navigate to Dashy with basic waiting, not networkidle
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  
  // Wait a bit for any redirects to happen
  await page.waitForTimeout(3000);
  
  console.log('Current URL:', page.url());
  
  // Check if we're already authenticated (on Dashy) or need to authenticate
  if (page.url().includes('dashy')) {
    console.log('Already authenticated or Dashy loaded');
    // Save the authentication state
    await page.context().storageState({ path: authFile });
    return;
  }
  
  // If we got redirected but the URL has 0.0.0.0:9000, fix it
  let currentUrl = page.url();
  if (currentUrl.includes('0.0.0.0:9000')) {
    console.log('Fixing redirect URL from 0.0.0.0:9000 to zoi.local:9000');
    const fixedUrl = currentUrl.replace('0.0.0.0:9000', 'zoi.local:9000');
    console.log('Navigating to fixed URL:', fixedUrl);
    await page.goto(fixedUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    currentUrl = page.url();
    console.log('New URL after fix:', currentUrl);
  }
  
  // Check if we're on Authentik login page
  if (currentUrl.includes('authentik') || currentUrl.includes('zoi.local:9000')) {
    console.log('On Authentik login page, logging in...');
    
    // Wait for login form to be available
    await page.waitForSelector('input[name="uid_field"]', { timeout: 10000 });
    
    // Fill in credentials (using bootstrap admin)
    await page.fill('input[name="uid_field"]', 'admin@zoi.local');
    await page.fill('input[name="password"]', 'change-me-authentik-admin');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for redirect back to Dashy
    await page.waitForURL(/dashy/, { timeout: 15000 });
    console.log('Successfully authenticated and redirected to Dashy');
  } else {
    console.log('Unexpected URL after redirect fix:', currentUrl);
    throw new Error(`Unexpected URL: ${currentUrl}`);
  }
  
  // Save the authentication state
  await page.context().storageState({ path: authFile });
  console.log('Authentication state saved');
}); 