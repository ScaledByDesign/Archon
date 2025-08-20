# Flowise Configuration Deployment Script (PowerShell)
# ====================================================

param(
    [string]$ConfigFile = "",
    [string]$FlowiseUrl = "http://localhost:7070",
    [string]$ApiKey = ""
)

Write-Host "🌊 Flowise Configuration Deployment Tool" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$FlowiseApiBase = "$FlowiseUrl/api/v1"
$ConfigDir = Join-Path $PSScriptRoot "..\flowise-configs"
$Headers = @{"Content-Type" = "application/json"}

if ($ApiKey) {
    $Headers["Authorization"] = "Bearer $ApiKey"
}

function Test-FlowiseHealth {
    Write-Host "🔍 Checking Flowise health..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$FlowiseUrl/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Flowise is accessible" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "❌ Flowise health check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $false
}

function Get-ExistingChatflows {
    try {
        $response = Invoke-RestMethod -Uri "$FlowiseApiBase/chatflows" -Headers $Headers -TimeoutSec 30
        return $response
    } catch {
        Write-Host "❌ Failed to get existing chatflows: $($_.Exception.Message)" -ForegroundColor Red
        return @()
    }
}

function Deploy-Chatflow {
    param(
        [string]$ConfigFilePath
    )
    
    $configFileName = Split-Path $ConfigFilePath -Leaf
    Write-Host "📁 Loading configuration: $configFileName" -ForegroundColor Yellow
    
    try {
        $chatflowConfig = Get-Content $ConfigFilePath -Raw | ConvertFrom-Json
    } catch {
        Write-Host "❌ Failed to load config file: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Validate required fields
    $requiredFields = @('name', 'nodes', 'edges')
    foreach ($field in $requiredFields) {
        if (-not $chatflowConfig.PSObject.Properties[$field]) {
            Write-Host "❌ Missing required field: $field" -ForegroundColor Red
            return $false
        }
    }
    
    # Check if chatflow already exists
    $existingChatflows = Get-ExistingChatflows
    $existingChatflow = $existingChatflows | Where-Object { $_.name -eq $chatflowConfig.name }
    
    $body = $chatflowConfig | ConvertTo-Json -Depth 20
    
    try {
        if ($existingChatflow) {
            Write-Host "🔄 Updating existing chatflow: $($chatflowConfig.name)" -ForegroundColor Cyan
            $response = Invoke-RestMethod -Uri "$FlowiseApiBase/chatflows/$($existingChatflow.id)" -Method PUT -Headers $Headers -Body $body -TimeoutSec 60
        } else {
            Write-Host "🆕 Creating new chatflow: $($chatflowConfig.name)" -ForegroundColor Cyan
            $response = Invoke-RestMethod -Uri "$FlowiseApiBase/chatflows" -Method POST -Headers $Headers -Body $body -TimeoutSec 60
        }
        
        $chatflowId = if ($response.id) { $response.id } else { "unknown" }
        Write-Host "✅ Successfully deployed chatflow: $($chatflowConfig.name) (ID: $chatflowId)" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "❌ Failed to deploy chatflow: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Deploy-AllConfigs {
    Write-Host "🚀 Starting batch deployment of Flowise configurations..." -ForegroundColor Green
    Write-Host ""
    
    if (-not (Test-FlowiseHealth)) {
        Write-Host "❌ Flowise is not accessible. Please ensure it's running." -ForegroundColor Red
        return $false
    }
    
    $configFiles = Get-ChildItem -Path $ConfigDir -Filter "*chatflow.json" -File
    if ($configFiles.Count -eq 0) {
        Write-Host "❌ No chatflow configuration files found in $ConfigDir" -ForegroundColor Red
        return $false
    }
    
    Write-Host "📁 Found $($configFiles.Count) configuration files" -ForegroundColor Cyan
    Write-Host ""
    
    $successCount = 0
    foreach ($configFile in $configFiles) {
        if (Deploy-Chatflow -ConfigFilePath $configFile.FullName) {
            $successCount++
        }
        Write-Host ""  # Add spacing between deployments
    }
    
    Write-Host "🎉 Deployment complete: $successCount/$($configFiles.Count) chatflows deployed successfully" -ForegroundColor Green
    return $successCount -eq $configFiles.Count
}

function Test-ConfigFile {
    param(
        [string]$ConfigFilePath
    )
    
    $configFileName = Split-Path $ConfigFilePath -Leaf
    Write-Host "🔍 Validating configuration: $configFileName" -ForegroundColor Yellow
    
    try {
        $config = Get-Content $ConfigFilePath -Raw | ConvertFrom-Json
    } catch {
        Write-Host "❌ Invalid JSON: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Basic validation
    $requiredFields = @('name', 'nodes', 'edges')
    foreach ($field in $requiredFields) {
        if (-not $config.PSObject.Properties[$field]) {
            Write-Host "❌ Missing required field: $field" -ForegroundColor Red
            return $false
        }
    }
    
    # Validate nodes
    if (-not $config.nodes -or $config.nodes.Count -eq 0) {
        Write-Host "❌ Nodes must be a non-empty array" -ForegroundColor Red
        return $false
    }
    
    # Validate edges
    if (-not ($config.edges -is [array])) {
        Write-Host "❌ Edges must be an array" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ Configuration is valid" -ForegroundColor Green
    return $true
}

# Main execution
if ($ConfigFile) {
    # Deploy specific file
    $configPath = if (Test-Path $ConfigFile) { $ConfigFile } else { Join-Path $ConfigDir $ConfigFile }
    
    if (-not (Test-Path $configPath)) {
        Write-Host "❌ Configuration file not found: $configPath" -ForegroundColor Red
        exit 1
    }
    
    if (Test-ConfigFile -ConfigFilePath $configPath) {
        $success = Deploy-Chatflow -ConfigFilePath $configPath
        exit $(if ($success) { 0 } else { 1 })
    } else {
        exit 1
    }
} else {
    # Deploy all configurations
    $success = Deploy-AllConfigs
    exit $(if ($success) { 0 } else { 1 })
}

# Example usage:
# .\deploy_flowise_configs.ps1                                    # Deploy all configs
# .\deploy_flowise_configs.ps1 -ConfigFile "litellm-development-chatflow.json"  # Deploy specific config
# .\deploy_flowise_configs.ps1 -FlowiseUrl "http://localhost:7070" -ApiKey "your-api-key"  # With custom settings
