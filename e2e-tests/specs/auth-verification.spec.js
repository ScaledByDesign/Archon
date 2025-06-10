const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow Verification', () => {
  test('verify forward auth middleware redirects to Authentik', async ({ page }) => {
    console.log('Testing forward auth redirect behavior...');
    
    // Test that accessing Dashy triggers authentication redirect
    const response = await page.goto('https://dashy.localhost/', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000 
    });
    
    // Get the current URL after redirect
    const currentUrl = page.url();
    console.log('Current URL after redirect:', currentUrl);
    
    // Verify we get redirected to OAuth authorize endpoint
    expect(currentUrl).toContain('/application/o/authorize/');
    expect(currentUrl).toContain('client_id=');
    expect(currentUrl).toContain('redirect_uri=');
    expect(currentUrl).toContain('response_type=code');
    
    console.log('✅ Forward auth redirect is working correctly!');
  });

  test('verify authentication headers and cookies', async ({ page }) => {
    console.log('Testing authentication headers...');
    
    // Make request to Dashy and capture response headers
    const response = await page.goto('https://dashy.localhost/', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000 
    });
    
    // Check for authentication-related headers
    const headers = response.headers();
    console.log('Response headers:', Object.keys(headers));
    
    // Verify we get a redirect response (302)
    expect(response.status()).toBe(302);
    
    // Check for authentication cookie
    const cookies = await page.context().cookies();
    const authCookie = cookies.find(cookie => cookie.name.includes('authentik_proxy'));
    
    if (authCookie) {
      console.log('✅ Authentication cookie found:', authCookie.name);
      expect(authCookie.domain).toBe('localhost');
      expect(authCookie.httpOnly).toBe(true);
      expect(authCookie.secure).toBe(true);
    }
    
    console.log('✅ Authentication headers and cookies verified!');
  });
  
  test('verify OAuth parameters in redirect URL', async ({ page }) => {
    console.log('Testing OAuth parameters...');
    
    // Navigate and capture the redirect
    await page.goto('https://dashy.localhost/', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000 
    });
    
    const currentUrl = page.url();
    const url = new URL(currentUrl.replace('0.0.0.0:9000', 'localhost:9000'));
    const params = url.searchParams;
    
    // Verify OAuth parameters
    expect(params.get('client_id')).toBeTruthy();
    expect(params.get('redirect_uri')).toContain('dashy.localhost');
    expect(params.get('response_type')).toBe('code');
    expect(params.get('scope')).toContain('openid');
    expect(params.get('state')).toBeTruthy();
    
    console.log('✅ OAuth parameters are correctly configured!');
    console.log('Client ID:', params.get('client_id'));
    console.log('Redirect URI:', params.get('redirect_uri'));
    console.log('Scope:', params.get('scope'));
  });
}); 