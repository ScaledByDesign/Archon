#!/bin/bash
# Setup /etc/hosts entries for local development

echo "🔧 Setting up local hosts entries..."
echo ""

# Check if entries already exist
if grep -q "dashy.zoi.local" /etc/hosts; then
    echo "✅ Host entries already exist"
    exit 0
fi

echo "📝 The following entries need to be added to /etc/hosts:"
echo ""
echo "127.0.0.1  dashy.zoi.local"
echo "127.0.0.1  auth.zoi.local"
echo "127.0.0.1  api.zoi.local"
echo "127.0.0.1  llm.zoi.local"
echo "127.0.0.1  traefik.zoi.local"
echo ""
echo "Run this command to add them:"
echo ""
echo "sudo sh -c 'echo \"127.0.0.1  dashy.zoi.local auth.zoi.local api.zoi.local llm.zoi.local traefik.zoi.local\" >> /etc/hosts'"
echo ""
echo "Or manually edit /etc/hosts with: sudo nano /etc/hosts"
