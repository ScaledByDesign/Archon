# Simple Dashboard Cleanup
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Cleaning up existing dashboards..." -ForegroundColor Cyan

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Get all existing dashboards
Write-Host "Finding existing dashboards..." -ForegroundColor Yellow
try {
    $dashResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/search?type=dash-db" -Headers $headers -TimeoutSec 10
    $dashboards = ($dashResponse.Content | ConvertFrom-Json)
    
    Write-Host "Found $($dashboards.Count) dashboards:" -ForegroundColor Cyan
    foreach ($dash in $dashboards) {
        Write-Host "  - $($dash.title)" -ForegroundColor White
    }
    
    # Delete each dashboard
    Write-Host "Deleting dashboards..." -ForegroundColor Yellow
    $deletedCount = 0
    
    foreach ($dash in $dashboards) {
        try {
            $deleteResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/uid/$($dash.uid)" -Method DELETE -Headers $headers
            Write-Host "  Deleted: $($dash.title)" -ForegroundColor Green
            $deletedCount++
        } catch {
            Write-Host "  Failed to delete: $($dash.title)" -ForegroundColor Red
        }
    }
    
    Write-Host "Cleanup complete! Deleted $deletedCount dashboards" -ForegroundColor Green
    
} catch {
    Write-Host "Failed to retrieve dashboards: $($_.Exception.Message)" -ForegroundColor Red
}

# Verify cleanup
Write-Host "Verifying cleanup..." -ForegroundColor Yellow
try {
    $verifyResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/search?type=dash-db" -Headers $headers -TimeoutSec 10
    $remainingDashboards = ($verifyResponse.Content | ConvertFrom-Json)
    
    if ($remainingDashboards.Count -eq 0) {
        Write-Host "All dashboards successfully removed!" -ForegroundColor Green
    } else {
        Write-Host "$($remainingDashboards.Count) dashboards still remain" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not verify cleanup" -ForegroundColor Yellow
}

Write-Host "Dashboard cleanup complete!" -ForegroundColor Green
Write-Host "Ready to create fresh working dashboards." -ForegroundColor Cyan
