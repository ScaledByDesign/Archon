#!/bin/bash
# Setup /etc/hosts entries for local development

echo "🔧 Setting up local hosts entries..."
echo ""

# Check if entries already exist
if grep -q "dashy.localhost" /etc/hosts; then
    echo "✅ Host entries already exist"
    exit 0
fi

echo "📝 The following entries need to be added to /etc/hosts:"
echo ""
echo "127.0.0.1  dashy.localhost"
echo "127.0.0.1  auth.localhost"
echo "127.0.0.1  api.localhost"
echo "127.0.0.1  llm.localhost"
echo "127.0.0.1  traefik.localhost"
echo ""
echo "Run this command to add them:"
echo ""
echo "sudo sh -c 'echo \"127.0.0.1  dashy.localhost auth.localhost api.localhost llm.localhost traefik.localhost\" >> /etc/hosts'"
echo ""
echo "Or manually edit /etc/hosts with: sudo nano /etc/hosts"
