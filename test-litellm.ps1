# Test LiteLLM API
$headers = @{
    "Authorization" = "Bearer sk-wqn0xwq_vha4MVM2yzw"
    "Content-Type" = "application/json"
}

# Test 1: Get available models
Write-Host "=== Testing Models Endpoint ===" -ForegroundColor Green
try {
    $models = Invoke-RestMethod -Uri "http://localhost:7010/v1/models" -Method GET -Headers $headers
    Write-Host "Available Models:" -ForegroundColor Yellow
    $models.data | ForEach-Object { Write-Host "  - $($_.id)" }
} catch {
    Write-Host "Error getting models: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Simple chat completion
Write-Host "`n=== Testing Chat Completion ===" -ForegroundColor Green
$body = @{
    model = "zoi-thinker"
    messages = @(
        @{
            role = "user"
            content = "Hello! What is 2+2? Please give a brief answer."
        }
    )
    max_tokens = 100
    temperature = 0.7
} | ConvertTo-Json -Depth 3

try {
    $response = Invoke-RestMethod -Uri "http://localhost:7010/v1/chat/completions" -Method POST -Headers $headers -Body $body
    Write-Host "Response:" -ForegroundColor Yellow
    Write-Host "  Model: $($response.model)"
    Write-Host "  Content: $($response.choices[0].message.content)"
    Write-Host "  Tokens Used: $($response.usage.total_tokens)"
} catch {
    Write-Host "Error in chat completion: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorDetails = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorDetails)
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error Details: $errorBody" -ForegroundColor Red
    }
}

# Test 3: Health check
Write-Host "`n=== Testing Health Endpoint ===" -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:7010/health" -Method GET -Headers $headers
    Write-Host "Health Status:" -ForegroundColor Yellow
    Write-Host "  Healthy Endpoints: $($health.healthy_endpoints.Count)"
    $health.healthy_endpoints | ForEach-Object { 
        Write-Host "    - $($_.api_base) (timeout: $($_.timeout)s)"
    }
} catch {
    Write-Host "Error getting health: $($_.Exception.Message)" -ForegroundColor Red
}
