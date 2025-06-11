#!/usr/bin/env python3
"""
Authentik Forward Auth Setup Script
Creates the necessary proxy provider, application, and outpost configuration
"""

from authentik.providers.proxy.models import ProxyProvider
from authentik.core.models import Application
from authentik.flows.models import Flow
from authentik.outposts.models import Outpost
from authentik.providers.proxy.models import ProxyMode

# Get the default flows
try:
    auth_flow = Flow.objects.get(slug="default-authorization-flow")
except Flow.DoesNotExist:
    auth_flow = Flow.objects.get(slug="default-provider-authorization-implicit-consent")

try:
    invalidation_flow = Flow.objects.get(slug="default-invalidation-flow")
except Flow.DoesNotExist:
    invalidation_flow = None

print("Creating proxy provider...")
provider, created = ProxyProvider.objects.get_or_create(
    name="Traefik Forward Auth",
    defaults={
        "mode": ProxyMode.FORWARD_SINGLE,
        "external_host": "http://zoi.local:9000",
        "authorization_flow": auth_flow,
        "invalidation_flow": invalidation_flow,
    }
)

if created:
    print("✅ Created new proxy provider")
else:
    print("✅ Using existing proxy provider")
    # Update external_host if needed
    provider.external_host = "http://zoi.local:9000"
    provider.save()

print("Creating application...")
app, created = Application.objects.get_or_create(
    slug="traefik-forward-auth",
    defaults={
        "name": "Traefik Forward Auth App",
        "provider": provider,
    }
)

if created:
    print("✅ Created new application")
else:
    print("✅ Using existing application")
    # Ensure provider is linked
    app.provider = provider
    app.save()

print("Configuring embedded outpost...")
try:
    outpost = Outpost.objects.get(name="authentik Embedded Outpost")
    outpost.providers.add(provider)
    print("✅ Added provider to embedded outpost")
except Outpost.DoesNotExist:
    print("❌ No embedded outpost found")

print("\n🎉 Forward auth setup complete!")
print(f"Application slug: {app.slug}")
print(f"Provider external host: {provider.external_host}")
print(f"Endpoint: /application/o/{app.slug}/")
