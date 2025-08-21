# Fix Grafana Datasource Configuration
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Fixing Grafana Datasource Configuration..." -ForegroundColor Cyan
Write-Host "=" * 50

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# First, let's see what datasources exist
Write-Host "Checking existing datasources..." -ForegroundColor Yellow
try {
    $dsResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources" -Headers $headers
    $datasources = ($dsResponse.Content | ConvertFrom-Json)
    
    Write-Host "Found $($datasources.Count) datasources:" -ForegroundColor Cyan
    foreach ($ds in $datasources) {
        Write-Host "  ID: $($ds.id), Name: $($ds.name), Type: $($ds.type), URL: $($ds.url)" -ForegroundColor White
    }
} catch {
    Write-Host "Failed to get datasources: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Find and delete the incorrect Prometheus datasource
$promDS = $datasources | Where-Object { $_.type -eq "prometheus" }
if ($promDS) {
    Write-Host "Deleting incorrect Prometheus datasource (ID: $($promDS.id))..." -ForegroundColor Yellow
    try {
        $deleteResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources/$($promDS.id)" -Method DELETE -Headers $headers
        Write-Host "Datasource deleted successfully" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not delete datasource: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Create new correct Prometheus datasource
Write-Host "Creating new Prometheus datasource..." -ForegroundColor Yellow
$newDatasource = @{
    name = "Prometheus"
    type = "prometheus"
    url = "http://host.docker.internal:9090"
    access = "proxy"
    isDefault = $true
    basicAuth = $false
    jsonData = @{
        httpMethod = "POST"
        queryTimeout = "60s"
        timeInterval = "15s"
    }
} | ConvertTo-Json -Depth 5

try {
    $createResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources" -Method POST -Headers $headers -Body $newDatasource
    $newDS = ($createResponse.Content | ConvertFrom-Json)
    Write-Host "New Prometheus datasource created with ID: $($newDS.id)" -ForegroundColor Green
    
    # Test the datasource
    Write-Host "Testing datasource connection..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    try {
        $testUrl = "$GrafanaUrl/api/datasources/$($newDS.id)/proxy/api/v1/query?query=up"
        $testResponse = Invoke-WebRequest -Uri $testUrl -Headers $headers -TimeoutSec 15
        $testResult = ($testResponse.Content | ConvertFrom-Json)
        
        if ($testResult.data.result.Count -gt 0) {
            Write-Host "Datasource test SUCCESSFUL!" -ForegroundColor Green
            Write-Host "Found $($testResult.data.result.Count) metrics" -ForegroundColor Cyan
            
            # Show sample data
            Write-Host "Sample metrics:" -ForegroundColor Cyan
            foreach ($result in $testResult.data.result | Select-Object -First 5) {
                $job = $result.metric.job
                $value = $result.value[1]
                Write-Host "  $job = $value" -ForegroundColor White
            }
        } else {
            Write-Host "Datasource connected but returned no data" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Datasource test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "Failed to create datasource: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Datasource Fix Complete!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Refresh your Grafana dashboard" -ForegroundColor White
Write-Host "2. Data should now appear in all panels" -ForegroundColor White
Write-Host "3. If still no data, check panel queries" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard URL: $GrafanaUrl/d/cd888a69-3c0e-4ec6-a006-2a185298927d/zoi-complete-monitoring-dashboard" -ForegroundColor Cyan
