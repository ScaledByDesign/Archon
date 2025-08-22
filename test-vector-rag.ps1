# Test Vector Database and RAG functionality
$headers = @{
    "Authorization" = "Bearer sk-wqn0xwq_vha4MVM2yzw"
    "Content-Type" = "application/json"
}

Write-Host "=== Testing Vector Database & RAG Setup ===" -ForegroundColor Green

# Test 1: Check Qdrant Collections
Write-Host "`n1. Checking Qdrant Collections..." -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "http://localhost:7060/collections" -Method GET
    Write-Host "Available Collections:" -ForegroundColor Cyan
    $collections.result.collections | ForEach-Object { 
        Write-Host "  - $($_.name) (points: $($_.points_count))" 
    }
} catch {
    Write-Host "Error accessing Qdrant: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Test Embedding Generation
Write-Host "`n2. Testing Embedding Generation..." -ForegroundColor Yellow
$embedBody = @{
    model = "zoi-embed"
    input = "Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently."
} | ConvertTo-Json -Depth 3

try {
    $embedResponse = Invoke-RestMethod -Uri "http://localhost:7010/v1/embeddings" -Method POST -Headers $headers -Body $embedBody
    Write-Host "SUCCESS! Embedding Generated:" -ForegroundColor Green
    Write-Host "  Model: $($embedResponse.model)"
    Write-Host "  Dimensions: $($embedResponse.data[0].embedding.Count)"
    Write-Host "  Tokens Used: $($embedResponse.usage.total_tokens)"
    Write-Host "  First 5 values: $($embedResponse.data[0].embedding[0..4] -join ', ')"
} catch {
    Write-Host "Error generating embeddings: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test RAG-Enhanced Chat (zoi-rag-helper)
Write-Host "`n3. Testing RAG-Enhanced Chat (zoi-rag-helper)..." -ForegroundColor Yellow
$ragBody = @{
    model = "zoi-rag-helper"
    messages = @(
        @{
            role = "user"
            content = "Can you explain how vector databases work in AI applications? Please be detailed."
        }
    )
    max_tokens = 300
    temperature = 0.7
} | ConvertTo-Json -Depth 3

try {
    $ragResponse = Invoke-RestMethod -Uri "http://localhost:7010/v1/chat/completions" -Method POST -Headers $headers -Body $ragBody
    Write-Host "SUCCESS! RAG Response:" -ForegroundColor Green
    Write-Host "  Model Used: $($ragResponse.model)"
    Write-Host "  Response Length: $($ragResponse.choices[0].message.content.Length) characters"
    Write-Host "  Tokens Used: $($ragResponse.usage.total_tokens)"
    Write-Host "  Response Preview:" -ForegroundColor Cyan
    Write-Host "  $($ragResponse.choices[0].message.content.Substring(0, [Math]::Min(200, $ragResponse.choices[0].message.content.Length)))..."
} catch {
    Write-Host "Error with RAG chat: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error Details: $errorBody" -ForegroundColor Red
    }
}

# Test 4: Test RAG-Enhanced Thinking Model (zoi-rag-thinker)
Write-Host "`n4. Testing RAG-Enhanced Thinking Model (zoi-rag-thinker)..." -ForegroundColor Yellow
$ragThinkBody = @{
    model = "zoi-rag-thinker"
    messages = @(
        @{
            role = "user"
            content = "What are the key considerations when implementing a RAG system for production use?"
        }
    )
    max_tokens = 250
    temperature = 0.6
} | ConvertTo-Json -Depth 3

try {
    $ragThinkResponse = Invoke-RestMethod -Uri "http://localhost:7010/v1/chat/completions" -Method POST -Headers $headers -Body $ragThinkBody
    Write-Host "SUCCESS! RAG Thinker Response:" -ForegroundColor Green
    Write-Host "  Model Used: $($ragThinkResponse.model)"
    Write-Host "  Response Length: $($ragThinkResponse.choices[0].message.content.Length) characters"
    Write-Host "  Tokens Used: $($ragThinkResponse.usage.total_tokens)"
    Write-Host "  Response Preview:" -ForegroundColor Cyan
    Write-Host "  $($ragThinkResponse.choices[0].message.content.Substring(0, [Math]::Min(200, $ragThinkResponse.choices[0].message.content.Length)))..."
} catch {
    Write-Host "Error with RAG thinker: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Check Vector Store Configuration
Write-Host "`n5. Checking Vector Store Health..." -ForegroundColor Yellow
try {
    $qdrantInfo = Invoke-RestMethod -Uri "http://localhost:7060" -Method GET
    Write-Host "Qdrant Status:" -ForegroundColor Cyan
    Write-Host "  Version: $($qdrantInfo.version)"
    Write-Host "  Status: Healthy"
} catch {
    Write-Host "Qdrant health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Vector Database & RAG Test Complete ===" -ForegroundColor Green
