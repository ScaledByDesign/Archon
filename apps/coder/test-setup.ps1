# Refact Setup Test Script (PowerShell)
# Validates the complete Refact setup and integration

param(
    [switch]$Verbose
)

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARN] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Write-Header {
    param($Message)
    Write-Host $Message -ForegroundColor $Blue
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Fail {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

# Test counters
$TestsPassed = 0
$TestsFailed = 0

# Function to run a test
function Run-Test {
    param(
        [string]$TestName,
        [scriptblock]$TestCommand
    )
    
    Write-Status "Testing: $TestName"
    
    try {
        $result = & $TestCommand
        if ($result) {
            Write-Success $TestName
            $script:TestsPassed++
            return $true
        } else {
            Write-Fail $TestName
            $script:TestsFailed++
            return $false
        }
    } catch {
        Write-Fail "$TestName - Error: $($_.Exception.Message)"
        $script:TestsFailed++
        return $false
    }
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Run-Test "$Name HTTP endpoint" {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 10 -UseBasicParsing
            return $response.StatusCode -eq $ExpectedStatus
        } catch {
            return $false
        }
    }
}

# Function to test API endpoint with auth
function Test-ApiEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$AuthHeader
    )
    
    Run-Test "$Name API endpoint" {
        try {
            $headers = @{ "Authorization" = $AuthHeader }
            $response = Invoke-WebRequest -Uri $Url -Method Get -Headers $headers -TimeoutSec 10 -UseBasicParsing
            return $response.StatusCode -eq 200
        } catch {
            return $false
        }
    }
}

Write-Header "🧪 Refact Setup Test Suite"
Write-Host "============================"
Write-Host "Testing Refact.ai integration with Zoi ecosystem"
Write-Host ""

# Test 1: Docker Compose Configuration
Write-Header "📋 Configuration Tests"
Run-Test "Docker Compose configuration" {
    $result = docker compose config --quiet 2>&1
    return $LASTEXITCODE -eq 0
}

Run-Test "Coder stack configuration" {
    $result = docker compose -f apps/coder/docker-compose.yml config --quiet 2>&1
    return $LASTEXITCODE -eq 0
}

Write-Host ""

# Test 2: Network Configuration
Write-Header "🌐 Network Tests"
Run-Test "Zoi network exists" {
    $networks = docker network ls
    return $networks -match "zoi-network"
}

Write-Host ""

# Test 3: Core Services (if running)
Write-Header "🔧 Core Services Tests"
$postgresRunning = docker ps | Select-String "postgres"
if ($postgresRunning) {
    Test-HttpEndpoint "PostgreSQL health" "http://localhost:7063"
    Run-Test "PostgreSQL refact database" {
        $result = docker exec postgres psql -U postgres -lqt 2>$null
        return $result -match "refact"
    }
} else {
    Write-Warning "PostgreSQL not running - skipping database tests"
}

$redisRunning = docker ps | Select-String "redis"
if ($redisRunning) {
    Run-Test "Redis connectivity" {
        $result = docker exec redis redis-cli ping 2>$null
        return $result -match "PONG"
    }
} else {
    Write-Warning "Redis not running - skipping cache tests"
}

$litellmRunning = docker ps | Select-String "litellm"
if ($litellmRunning) {
    Test-HttpEndpoint "LiteLLM health" "http://localhost:7010/health"
    Test-ApiEndpoint "LiteLLM models API" "http://localhost:7010/v1/models" "Bearer sk-wqn0xwq_vha4MVM2yzw"
} else {
    Write-Warning "LiteLLM not running - skipping AI gateway tests"
}

$qdrantRunning = docker ps | Select-String "qdrant"
if ($qdrantRunning) {
    Test-HttpEndpoint "Qdrant health" "http://localhost:7060/health"
} else {
    Write-Warning "Qdrant not running - skipping vector database tests"
}

Write-Host ""

# Test 4: Refact Services (if running)
Write-Header "🤖 Refact Services Tests"
$refactServerRunning = docker ps | Select-String "refact-server"
if ($refactServerRunning) {
    Test-HttpEndpoint "Refact Server health" "http://localhost:7400/health"
    Test-ApiEndpoint "Refact Server admin API" "http://localhost:7400/v1/models" "Bearer refact-admin-token-zoi-2024-secure"
} else {
    Write-Warning "Refact Server not running - skipping server tests"
}

$refactAgentRunning = docker ps | Select-String "refact-agent"
if ($refactAgentRunning) {
    Test-HttpEndpoint "Refact Agent health" "http://localhost:7401/health"
    Test-HttpEndpoint "Refact Agent capabilities" "http://localhost:7401/v1/caps"
} else {
    Write-Warning "Refact Agent not running - skipping agent tests"
}

$refactGuiRunning = docker ps | Select-String "refact-gui"
if ($refactGuiRunning) {
    Test-HttpEndpoint "Refact GUI health" "http://localhost:7402/health"
} else {
    Write-Warning "Refact GUI not running - skipping GUI tests"
}

$refactDocsRunning = docker ps | Select-String "refact-docs"
if ($refactDocsRunning) {
    Test-HttpEndpoint "Refact Docs health" "http://localhost:7403/health"
} else {
    Write-Warning "Refact Docs not running - skipping docs tests"
}

Write-Host ""

# Test 5: File Structure Tests
Write-Header "📁 File Structure Tests"
Run-Test "Docker Compose file exists" { Test-Path "apps/coder/docker-compose.yml" }
Run-Test "Refact Server Dockerfile exists" { Test-Path "apps/coder/refact-server/Dockerfile.postgres" }
Run-Test "Refact Agent Dockerfile exists" { Test-Path "apps/coder/refact-agent/engine/Dockerfile" }
Run-Test "Refact GUI Dockerfile exists" { Test-Path "apps/coder/refact-agent/gui/Dockerfile" }
Run-Test "Configuration file exists" { Test-Path "apps/coder/config/bring-your-own-key.yaml" }
Run-Test "Integration documentation exists" { Test-Path "apps/coder/INTEGRATION.md" }
Run-Test "Setup scripts exist" { (Test-Path "apps/coder/start-refact.sh") -and (Test-Path "apps/coder/start-refact.bat") }

Write-Host ""

# Test 6: Environment Configuration Tests
Write-Header "⚙️ Environment Configuration Tests"
Run-Test "REFACT_SERVER_PORT defined" { (Get-Content ".env" | Select-String "REFACT_SERVER_PORT=7400") -ne $null }
Run-Test "REFACT_AGENT_PORT defined" { (Get-Content ".env" | Select-String "REFACT_AGENT_PORT=7401") -ne $null }
Run-Test "REFACT_GUI_PORT defined" { (Get-Content ".env" | Select-String "REFACT_GUI_PORT=7402") -ne $null }
Run-Test "REFACT_DOCS_PORT defined" { (Get-Content ".env" | Select-String "REFACT_DOCS_PORT=7403") -ne $null }
Run-Test "REFACT_ADMIN_TOKEN defined" { (Get-Content ".env" | Select-String "REFACT_ADMIN_TOKEN=") -ne $null }

Write-Host ""

# Test Results Summary
Write-Header "📊 Test Results Summary"
Write-Host "========================"
Write-Host "Tests Passed: $TestsPassed"
Write-Host "Tests Failed: $TestsFailed"
Write-Host "Total Tests: $($TestsPassed + $TestsFailed)"

if ($TestsFailed -eq 0) {
    Write-Success "🎉 All tests passed! Refact setup is ready."
    Write-Host ""
    Write-Host "🚀 Next Steps:"
    Write-Host "1. Start the services: .\start-refact.bat"
    Write-Host "2. Configure your IDE to use: http://localhost:7401"
    Write-Host "3. Set API key: refact-admin-token-zoi-2024-secure"
    Write-Host "4. Access web interface: http://localhost:7402"
    exit 0
} else {
    Write-Error "❌ Some tests failed. Please check the issues above."
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "- Check service logs: docker compose logs [service-name]"
    Write-Host "- Verify environment variables in .env file"
    Write-Host "- Ensure all required services are running"
    Write-Host "- Run health check: .\scripts\health-check.ps1"
    exit 1
}
