# Clean Up All Existing Dashboards
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "🧹 CLEANING UP ALL EXISTING DASHBOARDS" -ForegroundColor Cyan
Write-Host "=" * 60

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Get all existing dashboards
Write-Host "`n📋 Finding all existing dashboards..." -ForegroundColor Yellow
try {
    $dashResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/search?type=dash-db" -Headers $headers -TimeoutSec 10
    $dashboards = ($dashResponse.Content | ConvertFrom-Json)
    
    Write-Host "Found $($dashboards.Count) dashboards to clean up:" -ForegroundColor Cyan
    foreach ($dash in $dashboards) {
        Write-Host "  - $($dash.title) (UID: $($dash.uid))" -ForegroundColor White
    }
    
    # Delete each dashboard
    Write-Host "`nDeleting dashboards..." -ForegroundColor Yellow
    $deletedCount = 0
    
    foreach ($dash in $dashboards) {
        try {
            $deleteResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/uid/$($dash.uid)" -Method DELETE -Headers $headers
            Write-Host "  ✅ Deleted: $($dash.title)" -ForegroundColor Green
            $deletedCount++
        } catch {
            Write-Host "  ❌ Failed to delete: $($dash.title) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n✅ Cleanup complete! Deleted $deletedCount/$($dashboards.Count) dashboards" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Failed to retrieve dashboards: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verify cleanup
Write-Host "`nVerifying cleanup..." -ForegroundColor Yellow
try {
    $verifyResponse = Invoke-WebRequest -Uri "$GrafanaUrl/api/search?type=dash-db" -Headers $headers -TimeoutSec 10
    $remainingDashboards = ($verifyResponse.Content | ConvertFrom-Json)
    
    if ($remainingDashboards.Count -eq 0) {
        Write-Host "✅ All dashboards successfully removed!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  $($remainingDashboards.Count) dashboards still remain:" -ForegroundColor Yellow
        foreach ($dash in $remainingDashboards) {
            Write-Host "  - $($dash.title)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "⚠️  Could not verify cleanup" -ForegroundColor Yellow
}

Write-Host "`nDashboard cleanup complete!" -ForegroundColor Green
Write-Host "Ready to create fresh working dashboards with real data." -ForegroundColor Cyan
Write-Host "=" * 60
