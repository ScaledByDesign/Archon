# Simple Vector Database Test for Zoi AI Stack
Write-Host "🚀 Testing Vector Database & RAG Setup" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

$QDRANT_URL = "http://localhost:7060"
$LITELLM_URL = "http://localhost:7010"
$LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

$headers = @{
    "Authorization" = "Bearer $LITELLM_API_KEY"
    "Content-Type" = "application/json"
}

# Test 1: Check Qdrant Collections
Write-Host "`n1. Checking Qdrant Collections..." -ForegroundColor Yellow
try {
    $collections = Invoke-RestMethod -Uri "$QDRANT_URL/collections" -Method GET
    Write-Host "✅ Qdrant Available - Collections found:" -ForegroundColor Green
    $collections.result.collections | ForEach-Object { 
        Write-Host "   - $($_.name) (points: $($_.points_count))" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Qdrant Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Test Embedding Generation
Write-Host "`n2. Testing Embedding Generation..." -ForegroundColor Yellow
$embedBody = @{
    model = "zoi-embed"
    input = "Vector databases store high-dimensional vectors for AI applications."
} | ConvertTo-Json

try {
    $embedResponse = Invoke-RestMethod -Uri "$LITELLM_URL/v1/embeddings" -Method POST -Headers $headers -Body $embedBody
    Write-Host "✅ Embedding Generated Successfully!" -ForegroundColor Green
    Write-Host "   Model: $($embedResponse.model)" -ForegroundColor Cyan
    Write-Host "   Dimensions: $($embedResponse.data[0].embedding.Count)" -ForegroundColor Cyan
    Write-Host "   Tokens: $($embedResponse.usage.total_tokens)" -ForegroundColor Cyan
    Write-Host "   Sample values: $($embedResponse.data[0].embedding[0..4] -join ', ')..." -ForegroundColor Cyan
} catch {
    Write-Host "❌ Embedding Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test RAG-Enhanced Models
Write-Host "`n3. Testing RAG-Enhanced Models..." -ForegroundColor Yellow

# Test zoi-rag-helper
$ragHelperBody = @{
    model = "zoi-rag-helper"
    messages = @(
        @{
            role = "user"
            content = "Explain vector databases briefly."
        }
    )
    max_tokens = 150
} | ConvertTo-Json -Depth 3

try {
    $ragHelperResponse = Invoke-RestMethod -Uri "$LITELLM_URL/v1/chat/completions" -Method POST -Headers $headers -Body $ragHelperBody
    Write-Host "✅ RAG Helper Model Working!" -ForegroundColor Green
    Write-Host "   Model: $($ragHelperResponse.model)" -ForegroundColor Cyan
    Write-Host "   Tokens: $($ragHelperResponse.usage.total_tokens)" -ForegroundColor Cyan
    Write-Host "   Response: $($ragHelperResponse.choices[0].message.content.Substring(0, [Math]::Min(100, $ragHelperResponse.choices[0].message.content.Length)))..." -ForegroundColor White
} catch {
    Write-Host "❌ RAG Helper Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test zoi-rag-thinker
Write-Host "`n4. Testing RAG Thinker Model..." -ForegroundColor Yellow
$ragThinkerBody = @{
    model = "zoi-rag-thinker"
    messages = @(
        @{
            role = "user"
            content = "What are key benefits of using vector databases?"
        }
    )
    max_tokens = 150
} | ConvertTo-Json -Depth 3

try {
    $ragThinkerResponse = Invoke-RestMethod -Uri "$LITELLM_URL/v1/chat/completions" -Method POST -Headers $headers -Body $ragThinkerBody
    Write-Host "✅ RAG Thinker Model Working!" -ForegroundColor Green
    Write-Host "   Model: $($ragThinkerResponse.model)" -ForegroundColor Cyan
    Write-Host "   Tokens: $($ragThinkerResponse.usage.total_tokens)" -ForegroundColor Cyan
    Write-Host "   Response: $($ragThinkerResponse.choices[0].message.content.Substring(0, [Math]::Min(100, $ragThinkerResponse.choices[0].message.content.Length)))..." -ForegroundColor White
} catch {
    Write-Host "❌ RAG Thinker Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Check Qdrant Health
Write-Host "`n5. Checking Qdrant Health..." -ForegroundColor Yellow
try {
    $qdrantInfo = Invoke-RestMethod -Uri "$QDRANT_URL" -Method GET
    Write-Host "✅ Qdrant Health Check Passed!" -ForegroundColor Green
    Write-Host "   Version: $($qdrantInfo.version)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Qdrant Health Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Vector Database & RAG Test Complete!" -ForegroundColor Green
Write-Host "✅ Ready for RAG applications and semantic search!" -ForegroundColor Green
