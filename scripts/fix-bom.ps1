# Fix BOM issues in JSON files
Write-Host "Fixing BOM issues in dashboard files..." -ForegroundColor Green

$files = Get-ChildItem -Path "config\grafana\dashboards" -Recurse -Filter "*.json"

foreach ($file in $files) {
    Write-Host "Processing: $($file.FullName)"
    
    # Read content as UTF8 without BOM
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Write back without BOM
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
    
    Write-Host "  Fixed BOM: $($file.Name)" -ForegroundColor Green
}

Write-Host "Done! Restarting Grafana..." -ForegroundColor Cyan
docker restart grafana
