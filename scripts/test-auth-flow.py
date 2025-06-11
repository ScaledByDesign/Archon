#!/usr/bin/env python3
"""
Test Authentik authentication flow and Dashy access using Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import sys

async def test_auth_flow():
    print("🎭 Starting Playwright authentication flow test...")
    
    async with async_playwright() as p:
        # Launch browser with visible UI for debugging
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            args=[
                '--ignore-certificate-errors',  # For self-signed certs
                '--host-resolver-rules=MAP dashy.zoi.local 127.0.0.1, MAP auth.zoi.local 127.0.0.1'  # Map domains
            ]
        )
        
        context = await browser.new_context(
            ignore_https_errors=True  # For local development
        )
        
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to Dashy
            print("\n📍 Step 1: Navigating to Dashy dashboard...")
            # Try mapped domain first, then zoi.local:port
            dashy_urls = [
                'https://dashy.zoi.local',  # Should work with host mapping
                'https://zoi.local:443',    # Traefik HTTPS
                'http://zoi.local:4001'     # Direct Dashy port
            ]
            
            connected = False
            for url in dashy_urls:
                try:
                    print(f"   Trying: {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                    connected = True
                    print(f"   ✅ Connected to: {url}")
                    break
                except Exception as e:
                    print(f"   ❌ Failed: {str(e)}")
                    continue
            
            if not connected:
                print("   ❌ Could not connect to Dashy on any URL")
                return False
            
            # Check if we're redirected to Authentik
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            if 'auth.zoi.local' in current_url or 'authentik' in current_url:
                print("   ✅ Redirected to Authentik login page")
            else:
                print("   ❌ Not redirected to Authentik - checking page content...")
                content = await page.content()
                if "dashy" in content.lower():
                    print("   ⚠️  Dashy loaded directly - authentication might be disabled")
                    return False
            
            # Step 2: Login to Authentik
            print("\n📍 Step 2: Logging in to Authentik...")
            
            # Wait for login form
            await page.wait_for_selector('input[name="uid_field"]', timeout=10000)
            
            # Fill login form
            await page.fill('input[name="uid_field"]', 'admin@zoi.local')
            await page.fill('input[type="password"]', 'admin123!')
            
            # Submit form
            await page.click('button[type="submit"]')
            
            print("   ✅ Login form submitted")
            
            # Step 3: Wait for redirect back to Dashy
            print("\n📍 Step 3: Waiting for redirect to Dashy...")
            
            # Wait for either Dashy to load or an error
            try:
                await page.wait_for_function(
                    'window.location.hostname === "dashy.zoi.local" || document.querySelector(".dashy-header") !== null',
                    timeout=15000
                )
                
                current_url = page.url
                print(f"   Current URL: {current_url}")
                
                # Verify we're on Dashy
                if 'dashy.zoi.local' in current_url:
                    print("   ✅ Successfully redirected to Dashy")
                    
                    # Check if Dashy content loaded
                    dashy_content = await page.query_selector('.dashy-header, #app, [class*="dashy"]')
                    if dashy_content:
                        print("   ✅ Dashy dashboard loaded successfully!")
                        
                        # Take a screenshot for verification
                        await page.screenshot(path='dashy-authenticated.png')
                        print("   📸 Screenshot saved as dashy-authenticated.png")
                        
                        return True
                    else:
                        print("   ⚠️  On Dashy domain but content not loaded")
                        return False
                else:
                    print(f"   ❌ Not redirected to Dashy, still on: {current_url}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Timeout waiting for Dashy: {str(e)}")
                
                # Check current state
                current_url = page.url
                print(f"   Current URL: {current_url}")
                
                # Take error screenshot
                await page.screenshot(path='auth-error.png')
                print("   📸 Error screenshot saved as auth-error.png")
                
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            
            # Take error screenshot
            try:
                await page.screenshot(path='test-error.png')
                print("📸 Error screenshot saved as test-error.png")
            except:
                pass
                
            return False
            
        finally:
            await browser.close()

async def main():
    print("🔐 Testing Authentik Forward Authentication Flow")
    print("=" * 50)
    
    success = await test_auth_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ AUTHENTICATION FLOW TEST PASSED!")
        print("\nThe complete flow works:")
        print("1. Dashy redirects to Authentik ✓")
        print("2. Login works ✓")
        print("3. Redirect back to Dashy works ✓")
        print("4. Dashy dashboard loads ✓")
    else:
        print("❌ AUTHENTICATION FLOW TEST FAILED!")
        print("\nTroubleshooting steps:")
        print("1. Check if all services are running: docker ps")
        print("2. Check Authentik logs: docker logs authentik-server")
        print("3. Verify forward auth config exists in Authentik admin")
        print("4. Check Traefik logs: docker logs traefik")
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
