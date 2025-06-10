# 🚨 URGENT: Fix Authentik Hostname Redirect Issue

## 🎯 PROBLEM
Your Dashy service redirects to: `http://authentik-server:9000` (internal Docker hostname)  
**Should redirect to**: `https://auth.localhost` (external domain)

## ✅ SOLUTION: Complete Authentik Admin Setup

### Step 1: Access Authentik Admin
1. **Open browser** to: `http://localhost:9000/if/admin/`
2. **Login credentials**:
   - Username: `admin`
   - Password: `admin123!`

### Step 2: Create Proxy Provider ⭐
1. Navigate to **Applications** → **Providers** → **Create**
2. **Type**: Select `Proxy Provider`
3. **Configuration**:
   ```
   Name: Traefik Forward Auth
   Authorization flow: default-provider-authorization-explicit-consent
   Mode: Forward auth (domain level)  ⭐ CRITICAL
   External host: https://auth.localhost  ⭐ CRITICAL
   Cookie domain: localhost
   ```
4. **Save**

### Step 3: Create Application ⭐
1. Navigate to **Applications** → **Applications** → **Create**
2. **Configuration**:
   ```
   Name: Traefik Forward Auth
   Slug: traefik-forward-auth  ⭐ MUST MATCH MIDDLEWARE
   Provider: [Select the proxy provider from Step 2]
   Launch URL: https://auth.localhost
   ```
3. **Save**

### Step 4: Assign to Outpost
1. Navigate to **Applications** → **Outposts**
2. **Edit** the `authentik Embedded Outpost`
3. In **Selected applications**, add your application from Step 3
4. **Save**

---

## 🧪 TEST THE FIX

After completing the admin setup:

```bash
# Test should now redirect to external domain
curl -k -I https://dashy.localhost

# Expected result:
# Status: 302
# Location: https://auth.localhost/flows/...  ✅ (NOT authentik-server:9000)
```

---

## 📋 WHY THIS FIXES THE ISSUE

**Before**: Authentik doesn't know the external hostname, uses internal Docker name  
**After**: Proxy provider tells Authentik to use `https://auth.localhost` for redirects

**Critical Settings**:
- `External host: https://auth.localhost` → Sets correct redirect hostname  
- `Slug: traefik-forward-auth` → Matches middleware URL path
- `Mode: Forward auth (domain level)` → Enables forward authentication

---

## 🎉 SUCCESS INDICATORS

✅ **Fixed**: `curl -k -I https://dashy.localhost` redirects to `https://auth.localhost`  
✅ **Working**: Complete browser login flow from protected service  
✅ **Complete**: Access granted to Dashy after successful authentication

---

## 📞 NEXT STEPS

1. **Complete admin setup** (5 minutes)
2. **Test fix** with curl command above
3. **Verify browser flow** by accessing https://dashy.localhost
4. **Deploy more services** with `authentik-secure@file` middleware

Your configuration files are perfect - we just need this final admin step! 🚀
