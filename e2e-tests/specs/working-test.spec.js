import { test, expect } from '@playwright/test';

test('Test working URLs for Dashy authentication', async ({ page }) => {
  console.log('🚀 Testing different URL approaches...');
  
  // Test 1: Try HTTP first (should redirect to HTTPS)
  console.log('\n1️⃣ Testing HTTP dashy.zoi.local (should redirect)...');
  try {
    await page.goto('http://dashy.zoi.local', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000
    });
    console.log('✅ HTTP worked, current URL:', page.url());
    await page.screenshot({ path: 'test-results/http-dashy-test.png' });
  } catch (error) {
    console.log('❌ HTTP failed:', error.message);
  }

  // Test 2: Try direct Dashy port
  console.log('\n2️⃣ Testing direct Dashy port (zoi.local:4001)...');
  try {
    await page.goto('http://zoi.local:4001', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000
    });
    console.log('✅ Direct port worked, current URL:', page.url());
    await page.screenshot({ path: 'test-results/direct-dashy-test.png' });
  } catch (error) {
    console.log('❌ Direct port failed:', error.message);
  }

  // Test 3: Try Authentik directly
  console.log('\n3️⃣ Testing Authentik directly (zoi.local:9000)...');
  try {
    await page.goto('http://zoi.local:9000/if/admin/', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000
    });
    console.log('✅ Authentik worked, current URL:', page.url());
    console.log('📄 Page title:', await page.title());
    await page.screenshot({ path: 'test-results/authentik-test.png' });
  } catch (error) {
    console.log('❌ Authentik failed:', error.message);
  }

  // Test 4: Try HTTPS with certificate bypass
  console.log('\n4️⃣ Testing HTTPS dashy.zoi.local...');
  try {
    // Navigate and wait a bit longer
    await page.goto('https://dashy.zoi.local', { 
      waitUntil: 'domcontentloaded',
      timeout: 15000
    });
    await page.waitForTimeout(3000);
    console.log('✅ HTTPS worked, current URL:', page.url());
    await page.screenshot({ path: 'test-results/https-dashy-test.png' });
  } catch (error) {
    console.log('❌ HTTPS failed:', error.message);
  }

  console.log('\n✅ Test completed - check screenshots in test-results/');
}); 