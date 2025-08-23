# Simple Dashboard Format Fix
Write-Host "Fixing dashboard formats..." -ForegroundColor Green

$files = @(
    "config\grafana\dashboards\litellm\ai-services-monitoring.json",
    "config\grafana\dashboards\litellm\cost-tracking.json", 
    "config\grafana\dashboards\system\container-monitoring.json",
    "config\grafana\dashboards\system\database-monitoring.json",
    "config\grafana\dashboards\system\gpu-monitoring.json",
    "config\grafana\dashboards\system\system-overview.json"
)

foreach ($file in $files) {
    Write-Host "Processing: $file"
    
    $content = Get-Content $file -Raw
    $json = $content | ConvertFrom-Json
    
    if ($json.dashboard) {
        Write-Host "  Converting format..."
        $dashboard = $json.dashboard
        $newJson = $dashboard | ConvertTo-Json -Depth 20
        $newJson | Set-Content $file -Encoding UTF8
        Write-Host "  Fixed: $file" -ForegroundColor Green
    }
}

Write-Host "Done! Restarting Grafana..." -ForegroundColor Cyan
docker restart grafana
