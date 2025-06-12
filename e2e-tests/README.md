# Authentik + Traefik + Dashy E2E Tests

This directory contains comprehensive end-to-end tests for verifying the Authentik and Traefik integration with Dashy using Playwright.

## Test Structure

```
e2e-tests/
├── package.json              # Node.js dependencies
├── playwright.config.js      # Playwright configuration
├── specs/
│   ├── auth.setup.js                          # Authentication setup (runs first)
│   ├── dashy.spec.js                          # Dashy dashboard tests  
│   ├── integration.spec.js                    # Integration tests
│   └── authentik-traefik-forward-auth.spec.js # Forward auth middleware tests
├── auth-state/
│   └── user.json            # Stored authentication state (auto-generated)
└── test-results/            # Test artifacts (auto-generated)
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd e2e-tests
npm install
npx playwright install
```

### 2. Environment Variables

Create a `.env` file in the e2e-tests directory:

```bash
# Authentication credentials
AUTHENTIK_USER=admin
AUTHENTIK_PASSWORD=change-me-authentik-admin

# Base URLs
BASE_URL=https://dashy.zoi.local
AUTHENTIK_URL=http://auth.zoi.local

# Domain configuration
DOMAIN=zoi.local
```

### 3. Start Your Services

Ensure your docker-compose stack is running:

```bash
# From project root
docker-compose -f docker-compose.core.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.core.yml ps
```

### 4. Run Tests

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:auth        # Authentication tests only
npm run test:dashy       # Dashy dashboard tests only
npm run test:integration # Integration tests only
npm run test:forward-auth # Forward auth middleware tests
npm run test:all         # Run all test suites sequentially

# Environment setup check
npm run setup:env        # Verify environment is ready for testing

# Run with browser UI visible
npm run test:headed

# Debug mode
npm run test:debug

# Interactive UI mode
npm run test:ui
```

## Test Scenarios Covered

### Authentication Setup (`auth.setup.js`)
- Automated login to Authentik
- Authentication state preservation
- Session storage for subsequent tests

### Dashboard Tests (`dashy.spec.js`)
- Dashboard loading verification
- Service link visibility
- Status check functionality
- Responsive layout testing
- Search functionality

### Integration Tests (`integration.spec.js`)
- Unauthenticated user redirection
- Authentication persistence across reloads
- Multi-tab authentication
- Individual service authentication
- Auth header verification
- Logout functionality

### Forward Auth Middleware Tests (`authentik-traefik-forward-auth.spec.js`)
- **Forward Auth Endpoint Verification**: Ensures Traefik uses correct Authentik endpoint
- **Authentication Header Passing**: Verifies Authentik headers reach protected services
- **Domain Configuration**: Tests zoi.local subdomain authentication
- **Redirect Loop Prevention**: Ensures no infinite redirects occur
- **Complete Authentication Flow**: Full end-to-end authentication testing
- **Session Persistence**: Validates session maintenance across services
- **Error Handling**: Tests invalid credentials and service unavailability
- **Performance Testing**: Measures authentication timing and concurrent requests

## Configuration Details

### Playwright Configuration
- **Browser Support**: Chromium, Firefox, WebKit
- **Auth State**: Cached between tests for efficiency
- **Retries**: 2 retries on CI, 0 locally
- **Timeouts**: 30s for navigation, 30s for actions
- **Screenshots**: On failure only
- **Videos**: On failure only
- **Traces**: On first retry

### Authentication Flow
1. Navigate to Dashy URL
2. Automatic redirect to Authentik if not authenticated
3. Fill login form with credentials
4. Wait for redirect back to Dashy
5. Verify successful authentication
6. Save authentication state for subsequent tests

## Troubleshooting

### Common Issues

**Tests fail with "Navigation timeout"**
- Ensure all services are running and healthy
- Check that domain resolution is working (add to /etc/hosts if needed)
- Verify SSL certificates are accepted

**Authentication setup fails**
- Check AUTHENTIK_USER and AUTHENTIK_PASSWORD environment variables
- Verify Authentik is accessible at the configured URL
- Ensure Authentik admin user exists with correct credentials

**Services show as unauthenticated**
- Verify Traefik middleware configuration
- Check that authentik-forward-auth middleware is applied to services
- Ensure Authentik outpost is configured correctly

**Status checks fail**
- Some services may take time to become healthy
- Status check URLs may need adjustment based on your service configuration
- Network connectivity between services

### Debug Commands

```bash
# Check service health
docker-compose -f docker-compose.core.yml ps

# View service logs
docker-compose -f docker-compose.core.yml logs authentik-server
docker-compose -f docker-compose.core.yml logs traefik
docker-compose -f docker-compose.core.yml logs dashy

# Test manual authentication
curl -k -I https://dashy.zoi.local
curl -k -I http://auth.zoi.local

# View Playwright test results
npm run show-report

# View detailed trace for failed tests
npm run show-trace
```

## Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Install dependencies
  run: |
    cd e2e-tests
    npm ci

- name: Install Playwright
  run: |
    cd e2e-tests
    npx playwright install --with-deps

- name: Start services
  run: docker-compose -f docker-compose.core.yml up -d

- name: Wait for services
  run: sleep 120

- name: Run E2E tests
  run: |
    cd e2e-tests
    npm test
  env:
    CI: true
    AUTHENTIK_USER: ${{ secrets.AUTHENTIK_USER }}
    AUTHENTIK_PASSWORD: ${{ secrets.AUTHENTIK_PASSWORD }}

- name: Upload test results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: playwright-report
    path: e2e-tests/test-results/
```

## Security Notes

- Authentication credentials are stored in environment variables
- Test authentication state is saved locally in `auth-state/user.json`
- Ensure test credentials are not committed to version control
- Use separate test user accounts for E2E testing in production environments 