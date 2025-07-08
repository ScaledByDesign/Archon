# Portal App Organizer - Service Integration Documentation

> **Service Type**: Frontend Dashboard  
> **Integration Date**: 2025-07-08  
> **Protocol Version**: 1.0  
> **Status**: ✅ Fully Integrated

## 📋 **Service Overview**

The Portal App Organizer serves as the main dashboard interface for the Zoi infrastructure, providing a centralized location for users to access all available services. It features a modern, responsive UI with mobile support and integrates with Authentik for SSO authentication.

### **Key Features**
- 🎯 Centralized service dashboard
- 📱 Mobile and tablet responsive design
- 🔐 Authentik SSO integration
- 🎨 Modern UI with dark theme
- 📊 Service status monitoring
- 🔄 Drag-and-drop app reordering
- 📂 Collapsible service groups
- ⚙️ Settings and configuration management

## 🏗️ **Architecture Details**

### **Technology Stack**
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict mode
- **Styling**: Tailwind CSS
- **Authentication**: Authentik Forward Auth
- **Storage**: Local JSON file storage
- **Container**: Docker with multi-stage build

### **Network Configuration**
- **Frontend Network**: Web-facing traffic via Traefik
- **Backend Network**: Internal service communication
- **Auth Network**: Authentik integration
- **Monitoring Network**: Dashboard and monitoring integration

### **Port Configuration**
- **Internal Port**: 3000
- **External Port**: 3000
- **Health Check**: Process monitoring

## 🔧 **Configuration Files**

### **Environment Configuration**
**File**: `config/portal/portal.env`

```bash
# Service Configuration
PORTAL_HOST=portal.${DOMAIN:-zoi.local}
PORTAL_PORT=3000
PORTAL_PROTOCOL=http

# Next.js Configuration
NODE_ENV=production
PORT=3000
HOSTNAME=0.0.0.0

# OAuth2 Configuration (Authentik integration)
PORTAL_OAUTH_CLIENT_ID=${PORTAL_OAUTH_CLIENT_ID:-portal-oauth-client}
PORTAL_OAUTH_CLIENT_SECRET=${PORTAL_OAUTH_CLIENT_SECRET:-change-me-portal-oauth-secret}
AUTHENTIK_ISSUER=${AUTHENTIK_ISSUER:-http://auth.zoi.local/application/o/portal-oauth}

# Authentication Configuration
PORTAL_AUTH_ENABLED=${PORTAL_AUTH_ENABLED:-true}
PORTAL_AUTH_PROVIDER=${PORTAL_AUTH_PROVIDER:-authentik}

# Security Configuration
PORTAL_SESSION_SECRET=${PORTAL_SESSION_SECRET:-change-me-portal-session-secret}
PORTAL_SECURE_COOKIES=${PORTAL_SECURE_COOKIES:-false}
```

### **Docker Compose Configuration**
**Location**: `docker-compose.yml` - Portal service definition

```yaml
  portal:
    build:
      context: ./portal
      dockerfile: Dockerfile
    container_name: portal
    restart: unless-stopped
    ports:
      - "3000:3000"
    env_file:
      - ./config/portal/portal.env
    volumes:
      - portal_data:/app/data
      - /etc/localtime:/etc/localtime:ro
    healthcheck:
      test: ["CMD-SHELL", "ps aux | grep '[n]ext-server' || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - frontend_network
      - backend_network
      - auth_network
      - monitoring_network
    depends_on:
      traefik:
        condition: service_healthy
      authentik-server:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      
      # Main Portal UI with authentication
      - "traefik.http.routers.portal.rule=Host(`portal.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.portal.entrypoints=web"
      - "traefik.http.routers.portal.middlewares=authentik-forward-auth@file"
      - "traefik.http.services.portal.loadbalancer.server.port=3000"
      
      # Authentik Forward Auth Outpost
      - "traefik.http.routers.portal-outpost.rule=Host(`portal.${DOMAIN:-zoi.local}`) && PathPrefix(`/outpost.goauthentik.io/`)"
      - "traefik.http.routers.portal-outpost.entrypoints=web"
      - "traefik.http.routers.portal-outpost.service=authentik"
      - "traefik.http.routers.portal-outpost.priority=200"
```

### **Authentik Integration**
**Blueprint**: `config/portal/blueprints/portal-oauth-integration.yaml`

The Portal integrates with Authentik using:
- **Forward Auth Provider**: For UI access protection
- **OAuth2 Provider**: For API access (if needed)
- **Application Definition**: Portal App Organizer
- **Policy Bindings**: zoi-users group access

## 🚀 **Deployment Instructions**

### **Prerequisites**
- Docker and Docker Compose installed
- Traefik reverse proxy running
- Authentik authentication service running
- Required networks created

### **Deployment Steps**

1. **Build and Start Service**
   ```bash
   docker-compose up portal -d
   ```

2. **Verify Service Status**
   ```bash
   docker-compose ps portal
   docker-compose logs portal
   ```

3. **Test Connectivity**
   ```bash
   curl -I http://localhost:3000
   # Or visit http://portal.zoi.local
   ```

4. **Apply Authentik Blueprint** (if Authentik is running)
   ```bash
   # Blueprint is automatically loaded from config/portal/blueprints/
   ```

## 🔍 **Testing & Validation**

### **Health Checks**
- ✅ Container starts successfully
- ✅ Process monitoring health check passes
- ✅ Service accessible on port 3000
- ✅ API endpoints respond correctly
- ✅ UI loads and functions properly

### **Authentication Testing**
- ✅ Authentik forward auth integration
- ✅ SSO login flow
- ✅ Protected routes require authentication
- ✅ Logout functionality

### **Functionality Testing**
- ✅ Service list loads correctly
- ✅ App navigation works
- ✅ Mobile responsive design
- ✅ Settings and configuration
- ✅ Drag-and-drop reordering

## 🌐 **Access Information**

### **URLs**
- **Primary Access**: `http://portal.zoi.local`
- **Direct Access**: `http://localhost:3000` (development)
- **API Endpoint**: `http://portal.zoi.local/api/config`

### **Authentication**
- **Method**: Authentik Forward Auth
- **Required Group**: zoi-users
- **Login URL**: Automatically redirected via Authentik

## 📊 **Monitoring & Maintenance**

### **Log Locations**
```bash
# Container logs
docker-compose logs portal

# Application logs (if configured)
docker exec portal cat /app/logs/portal.log
```

### **Common Operations**
```bash
# Restart service
docker-compose restart portal

# Update configuration
docker-compose stop portal
# Edit config/portal/portal.env
docker-compose up portal -d

# View service status
docker-compose ps portal
```

### **Troubleshooting**
- **Service won't start**: Check Docker logs and environment configuration
- **Authentication issues**: Verify Authentik blueprint and forward auth setup
- **UI not loading**: Check Traefik routing and network connectivity
- **API errors**: Check Next.js application logs and configuration

## 🔄 **Integration Checklist**

### **Configuration** ✅
- [x] Environment file created with OAuth2 settings
- [x] Docker Compose service definition added
- [x] Volume definition added
- [x] Network assignments configured
- [x] Health check configured

### **Authentication** ✅
- [x] Authentik blueprint created
- [x] Forward auth provider configured
- [x] OAuth2 provider configured (optional)
- [x] Application and policy bindings set

### **Networking** ✅
- [x] Traefik routing configured
- [x] Forward auth middleware applied
- [x] Outpost routing configured
- [x] All required networks assigned

### **Testing** ✅
- [x] Service builds and starts successfully
- [x] Health checks pass
- [x] UI accessible and functional
- [x] API endpoints working
- [x] Authentication flow tested

### **Documentation** ✅
- [x] Integration documentation created
- [x] Environment variables documented
- [x] Deployment instructions provided
- [x] Troubleshooting guide included

## ✅ **Integration Status: COMPLETE**

The Portal App Organizer has been successfully integrated into the Zoi infrastructure following the complete service integration protocol. The service is now:

- 🔐 **Secured**: Protected by Authentik SSO authentication
- 🌐 **Accessible**: Available at `portal.zoi.local`
- 📊 **Monitored**: Health checks and logging configured
- 🔄 **Maintainable**: Follows established patterns and documentation standards
- 🎯 **Functional**: All features working as expected

The Portal serves as the main entry point for users to access all Zoi services in a secure, organized, and user-friendly manner.
