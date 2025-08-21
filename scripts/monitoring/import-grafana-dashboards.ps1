# Grafana Dashboard Import Script
# Automatically imports all custom dashboards into Grafana

param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Importing Grafana Dashboards..." -ForegroundColor Cyan
Write-Host "=" * 50

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Dashboard files to import
$dashboards = @(
    @{
        Name = "System Overview"
        Path = "config/grafana/dashboards/system/system-overview.json"
        Folder = "System"
    },
    @{
        Name = "Database Monitoring"
        Path = "config/grafana/dashboards/system/database-monitoring.json"
        Folder = "System"
    },
    @{
        Name = "Container Monitoring"
        Path = "config/grafana/dashboards/system/container-monitoring.json"
        Folder = "System"
    },
    @{
        Name = "Alerts Overview"
        Path = "config/grafana/dashboards/system/alerts-overview.json"
        Folder = "System"
    },
    @{
        Name = "LiteLLM Cost Tracking"
        Path = "config/grafana/dashboards/litellm/cost-tracking.json"
        Folder = "LiteLLM"
    },
    @{
        Name = "AI Services Monitoring"
        Path = "config/grafana/dashboards/litellm/ai-services-monitoring.json"
        Folder = "LiteLLM"
    }
)

# Function to create folder if it doesn't exist
function Create-GrafanaFolder {
    param($FolderName)
    
    try {
        $folderData = @{
            title = $FolderName
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/folders" -Method POST -Headers $headers -Body $folderData -ErrorAction SilentlyContinue
        Write-Host "  ✅ Created folder: $FolderName" -ForegroundColor Green
        return ($response.Content | ConvertFrom-Json).id
    } catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            # Folder already exists, get its ID
            $existingFolder = Invoke-WebRequest -Uri "$GrafanaUrl/api/folders/$FolderName" -Method GET -Headers $headers
            Write-Host "  📁 Folder exists: $FolderName" -ForegroundColor Yellow
            return ($existingFolder.Content | ConvertFrom-Json).id
        } else {
            Write-Host "  ❌ Failed to create folder $FolderName`: $($_.Exception.Message)" -ForegroundColor Red
            return $null
        }
    }
}

# Function to import dashboard
function Import-Dashboard {
    param($DashboardPath, $DashboardName, $FolderId)
    
    try {
        if (!(Test-Path $DashboardPath)) {
            Write-Host "  ❌ Dashboard file not found: $DashboardPath" -ForegroundColor Red
            return
        }
        
        $dashboardContent = Get-Content $DashboardPath -Raw | ConvertFrom-Json
        
        # Prepare import payload
        $importData = @{
            dashboard = $dashboardContent.dashboard
            folderId = $FolderId
            overwrite = $true
        } | ConvertTo-Json -Depth 20
        
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $importData
        Write-Host "  ✅ Imported: $DashboardName" -ForegroundColor Green
        
        $result = $response.Content | ConvertFrom-Json
        return $result.url
    } catch {
        Write-Host "  ❌ Failed to import $DashboardName`: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Wait for Grafana to be ready
Write-Host "🔍 Checking Grafana availability..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0

do {
    try {
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/health" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Grafana is ready!" -ForegroundColor Green
            break
        }
    } catch {
        $retryCount++
        if ($retryCount -ge $maxRetries) {
            Write-Host "❌ Grafana is not responding after $maxRetries attempts" -ForegroundColor Red
            exit 1
        }
        Write-Host "  ⏳ Waiting for Grafana... (attempt $retryCount/$maxRetries)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
} while ($retryCount -lt $maxRetries)

# Create folders and import dashboards
$importedDashboards = @()
$folderIds = @{}

Write-Host "`n📁 Creating folders and importing dashboards..." -ForegroundColor Yellow

foreach ($dashboard in $dashboards) {
    Write-Host "`nProcessing: $($dashboard.Name)" -ForegroundColor Cyan
    
    # Create or get folder ID
    if (!$folderIds.ContainsKey($dashboard.Folder)) {
        $folderId = Create-GrafanaFolder -FolderName $dashboard.Folder
        if ($folderId) {
            $folderIds[$dashboard.Folder] = $folderId
        } else {
            continue
        }
    }
    
    # Import dashboard
    $dashboardUrl = Import-Dashboard -DashboardPath $dashboard.Path -DashboardName $dashboard.Name -FolderId $folderIds[$dashboard.Folder]
    if ($dashboardUrl) {
        $importedDashboards += @{
            Name = $dashboard.Name
            Folder = $dashboard.Folder
            Url = "$GrafanaUrl$dashboardUrl"
        }
    }
}

# Configure Prometheus datasource
Write-Host "`n🔗 Configuring Prometheus datasource..." -ForegroundColor Yellow
try {
    $datasourceData = @{
        name = "Prometheus"
        type = "prometheus"
        url = "http://prometheus-test:9090"
        access = "proxy"
        isDefault = $true
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources" -Method POST -Headers $headers -Body $datasourceData -ErrorAction SilentlyContinue
    Write-Host "✅ Prometheus datasource configured" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "📊 Prometheus datasource already exists" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  Failed to configure datasource: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Display results
Write-Host "`n🎉 Dashboard Import Complete!" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📊 Imported Dashboards:" -ForegroundColor Cyan
foreach ($dashboard in $importedDashboards) {
    Write-Host "  📈 $($dashboard.Name) ($($dashboard.Folder))" -ForegroundColor White
    Write-Host "     $($dashboard.Url)" -ForegroundColor Gray
}

Write-Host "`n🌐 Access Information:" -ForegroundColor Cyan
Write-Host "  Grafana URL: $GrafanaUrl" -ForegroundColor White
Write-Host "  Username: $Username" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Open Grafana in your browser" -ForegroundColor White
Write-Host "  2. Navigate to Dashboards > Browse" -ForegroundColor White
Write-Host "  3. Explore the System and LiteLLM folders" -ForegroundColor White
Write-Host "  4. Customize dashboards as needed" -ForegroundColor White

Write-Host "`n✨ Monitoring dashboards are ready!" -ForegroundColor Green
