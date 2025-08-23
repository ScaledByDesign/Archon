# Fix Grafana Dashboard Format
# Converts dashboards from {dashboard: {...}} format to {...} format

Write-Host "🔧 Fixing Grafana Dashboard Format" -ForegroundColor Cyan
Write-Host "=" * 40

$dashboardPaths = @(
    "config\grafana\dashboards\zoi-complete-dashboard.json",
    "config\grafana\dashboards\litellm\cost-tracking.json",
    "config\grafana\dashboards\litellm\ai-services-monitoring.json",
    "config\grafana\dashboards\system\system-overview.json",
    "config\grafana\dashboards\system\container-monitoring.json",
    "config\grafana\dashboards\system\database-monitoring.json",
    "config\grafana\dashboards\system\alerts-overview.json",
    "config\grafana\dashboards\system\gpu-monitoring.json"
)

foreach ($path in $dashboardPaths) {
    if (Test-Path $path) {
        Write-Host "📝 Processing: $path" -ForegroundColor Yellow
        
        try {
            # Read the JSON file
            $content = Get-Content $path -Raw | ConvertFrom-Json
            
            # Check if it has the nested dashboard structure
            if ($content.dashboard) {
                Write-Host "  ✅ Converting nested dashboard format" -ForegroundColor Green
                
                # Extract the dashboard content
                $dashboard = $content.dashboard
                
                # Convert back to JSON with proper formatting
                $fixedJson = $dashboard | ConvertTo-Json -Depth 20
                
                # Write back to file
                $fixedJson | Set-Content $path -Encoding UTF8
                
                Write-Host "  ✅ Fixed: $path" -ForegroundColor Green
            } else {
                Write-Host "  ℹ️  Already in correct format: $path" -ForegroundColor Blue
            }
        }
        catch {
            Write-Host "  ❌ Error processing $path : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️  File not found: $path" -ForegroundColor Yellow
    }
}

}

Write-Host "`n🎯 Dashboard format fix complete!" -ForegroundColor Green
Write-Host "Now restart Grafana to reload dashboards:" -ForegroundColor Cyan
Write-Host "  docker restart grafana" -ForegroundColor White
