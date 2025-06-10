# Authentik Forward Auth Fix - Simple Solution

## Root Cause Found ✅
The Authentik embedded outpost exists and is type "proxy" but has **NO providers configured**. This is why `/outpost.goauthentik.io/auth/traefik` returns 404.

## Quick Fix Steps

### 1. Access Authentik Admin
- URL: http://localhost:9000/if/admin/
- Login: `admin@localhost` / `password`

### 2. Create Proxy Provider
Navigate to **Applications → Providers → Create**
- **Type**: Proxy Provider
- **Name**: `Traefik Forward Auth`
- **Authorization flow**: `default-provider-authorization-implicit-consent` (if available) or `Welcome to authentik!`
- **Mode**: `Forward auth (single application)`
- **External host**: `http://localhost:9000` 
- **Cookie domain**: `localhost`

### 3. Create Application  
Navigate to **Applications → Applications → Create**
- **Name**: `Traefik Forward Auth`
- **Slug**: `traefik-forward-auth` 
- **Provider**: Select the provider created above

### 4. Link Provider to Outpost
Navigate to **Applications → Outposts → authentik Embedded Outpost**
- **Providers**: Select the `Traefik Forward Auth` provider

### 5. Test
After saving, test the endpoint:
```bash
curl -I "http://localhost:9000/outpost.goauthentik.io/auth/traefik"
```

Should return authentication redirect instead of 404.

### 6. Test Forward Auth Flow
```bash  
curl -I "http://dashy.localhost"
```

Should redirect to Authentik login.

## Alternative: CLI Commands (if available)
If the web interface doesn't work, these would be the equivalent commands:
```bash
# Create provider
docker exec authentik-server python manage.py shell -c "
from authentik.providers.proxy.models import ProxyProvider
from authentik.flows.models import Flow
flow = Flow.objects.filter(slug='default-provider-authorization-implicit-consent').first()
if not flow:
    flow = Flow.objects.first()
provider = ProxyProvider.objects.create(
    name='Traefik Forward Auth',
    authorization_flow=flow,
    mode='forward_single',
    external_host='http://localhost:9000',
    cookie_domain='localhost'
)
print(f'Created provider: {provider.pk}')
"

# Link to outpost (would need provider ID from above)
docker exec authentik-server python manage.py shell -c "
from authentik.outposts.models import Outpost
from authentik.providers.proxy.models import ProxyProvider
outpost = Outpost.objects.get(name='authentik Embedded Outpost')
provider = ProxyProvider.objects.get(name='Traefik Forward Auth')
outpost.providers.add(provider)
outpost.save()
print('Linked provider to outpost')
"
```

## Expected Result
- `/outpost.goauthentik.io/auth/traefik` responds with auth redirect
- `dashy.localhost` redirects to Authentik login 
- After login, user can access Dashy
- Playwright tests pass 