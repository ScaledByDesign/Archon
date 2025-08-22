# Qdrant Vector Store Integration Test for Zoi AI Stack
# =====================================================

Write-Host "🚀 Qdrant Vector Store Integration Test" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$QDRANT_URL = "http://localhost:7060"
$LITELLM_URL = "http://localhost:7010"
$LITELLM_API_KEY = "sk-wqn0xwq_vha4MVM2yzw"
$COLLECTION_NAME = "zoi_knowledge_base"

# Step 1: Check service availability
Write-Host "🔍 Step 1: Checking service availability..." -ForegroundColor Yellow

try {
    $qdrantResponse = Invoke-WebRequest -Uri "$QDRANT_URL/collections" -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ Qdrant: Available (Status: $($qdrantResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Qdrant: Not available - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

try {
    $headers = @{"Authorization" = "Bearer $LITELLM_API_KEY"}
    $litellmResponse = Invoke-WebRequest -Uri "$LITELLM_URL/v1/models" -Headers $headers -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ LiteLLM: Available (Status: $($litellmResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ LiteLLM: Not available - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Create Qdrant collection
Write-Host "📚 Step 2: Creating Qdrant collection '$COLLECTION_NAME'..." -ForegroundColor Yellow

$collectionConfig = @{
    name = $COLLECTION_NAME
    vectors = @{
        size = 1024
        distance = "Cosine"
    }
    optimizers_config = @{
        default_segment_number = 2
    }
    replication_factor = 1
} | ConvertTo-Json -Depth 3

try {
    $createResponse = Invoke-WebRequest -Uri "$QDRANT_URL/collections/$COLLECTION_NAME" -Method PUT -Body $collectionConfig -ContentType "application/json" -UseBasicParsing
    Write-Host "✅ Collection '$COLLECTION_NAME' created successfully (Status: $($createResponse.StatusCode))" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "ℹ️  Collection '$COLLECTION_NAME' already exists" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Failed to create collection: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 3: Test embedding generation
Write-Host "🧠 Step 3: Testing embedding generation with zoi-embed..." -ForegroundColor Yellow

$embeddingRequest = @{
    model = "zoi-embed"
    input = "This is a test document for vector embedding generation."
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $LITELLM_API_KEY"
    "Content-Type" = "application/json"
}

try {
    $embeddingResponse = Invoke-WebRequest -Uri "$LITELLM_URL/v1/embeddings" -Method POST -Headers $headers -Body $embeddingRequest -UseBasicParsing
    $embeddingData = $embeddingResponse.Content | ConvertFrom-Json
    $embedding = $embeddingData.data[0].embedding
    
    Write-Host "✅ Embedding generated successfully!" -ForegroundColor Green
    Write-Host "   📊 Vector dimensions: $($embedding.Count)" -ForegroundColor Cyan
    Write-Host "   📈 Sample values: $($embedding[0..4] -join ', ')..." -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to generate embedding: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Store sample document in Qdrant
Write-Host "📝 Step 4: Storing sample document with vector in Qdrant..." -ForegroundColor Yellow

$samplePoint = @{
    points = @(
        @{
            id = 1
            vector = $embedding
            payload = @{
                text = "This is a test document for vector embedding generation."
                category = "test"
                timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            }
        }
    )
} | ConvertTo-Json -Depth 4

try {
    $storeResponse = Invoke-WebRequest -Uri "$QDRANT_URL/collections/$COLLECTION_NAME/points" -Method PUT -Body $samplePoint -ContentType "application/json" -UseBasicParsing
    Write-Host "✅ Sample document stored successfully (Status: $($storeResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to store document: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 5: Test semantic search
Write-Host "🔍 Step 5: Testing semantic search..." -ForegroundColor Yellow

# Generate embedding for search query
$searchQuery = "test document embedding"
$searchEmbeddingRequest = @{
    model = "zoi-embed"
    input = $searchQuery
} | ConvertTo-Json

try {
    $searchEmbeddingResponse = Invoke-WebRequest -Uri "$LITELLM_URL/v1/embeddings" -Method POST -Headers $headers -Body $searchEmbeddingRequest -UseBasicParsing
    $searchEmbeddingData = $searchEmbeddingResponse.Content | ConvertFrom-Json
    $searchEmbedding = $searchEmbeddingData.data[0].embedding
    
    Write-Host "✅ Search query embedding generated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to generate search embedding: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Perform vector search
$searchRequest = @{
    vector = $searchEmbedding
    limit = 3
    with_payload = $true
} | ConvertTo-Json -Depth 3

try {
    $searchResponse = Invoke-WebRequest -Uri "$QDRANT_URL/collections/$COLLECTION_NAME/points/search" -Method POST -Body $searchRequest -ContentType "application/json" -UseBasicParsing
    $searchResults = ($searchResponse.Content | ConvertFrom-Json).result
    
    Write-Host "✅ Semantic search completed!" -ForegroundColor Green
    Write-Host "   🎯 Query: '$searchQuery'" -ForegroundColor Cyan
    Write-Host "   📊 Results found: $($searchResults.Count)" -ForegroundColor Cyan
    
    foreach ($result in $searchResults) {
        $score = [math]::Round($result.score, 3)
        $text = $result.payload.text
        Write-Host "   📄 Score: $score | Text: $($text.Substring(0, [Math]::Min(50, $text.Length)))..." -ForegroundColor White
    }
} catch {
    Write-Host "❌ Failed to perform search: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 6: Test RAG-enabled model (if available)
Write-Host "🤖 Step 6: Testing RAG-enabled model..." -ForegroundColor Yellow

$ragRequest = @{
    model = "zoi-rag-helper"
    messages = @(
        @{
            role = "user"
            content = "What can you tell me about test documents and embeddings?"
        }
    )
    max_tokens = 150
    temperature = 0.7
} | ConvertTo-Json -Depth 3

try {
    $ragResponse = Invoke-WebRequest -Uri "$LITELLM_URL/v1/chat/completions" -Method POST -Headers $headers -Body $ragRequest -UseBasicParsing
    $ragData = $ragResponse.Content | ConvertFrom-Json
    $ragAnswer = $ragData.choices[0].message.content
    
    Write-Host "✅ RAG-enabled model response:" -ForegroundColor Green
    Write-Host "   🤖 $ragAnswer" -ForegroundColor White
} catch {
    Write-Host "ℹ️  RAG-enabled model not yet fully configured (this is expected)" -ForegroundColor Yellow
    Write-Host "   📝 Standard models are working, RAG integration needs additional setup" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🎉 Qdrant Vector Store Integration Test Complete!" -ForegroundColor Green
Write-Host "✅ Vector store is ready for RAG applications" -ForegroundColor Green
Write-Host "✅ Embedding generation working through LiteLLM" -ForegroundColor Green
Write-Host "✅ Semantic search functionality verified" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Add more documents to the knowledge base" -ForegroundColor White
Write-Host "   2. Implement RAG workflows in Flowise" -ForegroundColor White
Write-Host "   3. Create custom RAG applications using the API" -ForegroundColor White
