#!/bin/bash
# Open browser to test the authentication flow manually

echo "🌐 Opening browser for manual authentication test..."
echo ""
echo "📝 Instructions:"
echo "1. The browser will open to https://dashy.localhost"
echo "2. You may see a certificate warning - click 'Advanced' and 'Proceed'"
echo "3. You should be redirected to Authentik login"
echo "4. Login with: admin@localhost / admin123!"
echo "5. After login, you should see the Dashy dashboard"
echo ""
echo "⚠️  Note: If you get 'Cannot reach site' error:"
echo "   Add this to /etc/hosts:"
echo "   127.0.0.1  dashy.localhost auth.localhost"
echo ""

# Open the browser
open https://dashy.localhost

echo "Browser opened. Follow the instructions above to test authentication."
