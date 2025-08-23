# Enhanced Docker build script with comprehensive caching for Windows
param(
    [switch]$Clean,
    [string]$RegistryCache = "",
    [switch]$Verbose,
    [switch]$Help
)

# Configuration
$ImageName = "realtime-voice-chat"
$ImageTag = "latest"
$CacheDir = ".buildcache"

if ($Help) {
    Write-Host "Usage: .\build.ps1 [OPTIONS]"
    Write-Host "Options:"
    Write-Host "  -Clean              Clean build without cache"
    Write-Host "  -RegistryCache URL  Use registry cache (e.g., ghcr.io/org/app:buildcache)"
    Write-Host "  -Verbose            Verbose output"
    Write-Host "  -Help               Show this help"
    exit 0
}

Write-Host "🚀 Starting optimized Docker build with comprehensive caching..." -ForegroundColor Green

# Enable BuildKit for faster builds and cache mounts
$env:DOCKER_BUILDKIT = "1"
$env:BUILDKIT_PROGRESS = "plain"

# Clean build cache if requested
if ($Clean) {
    Write-Host "🧹 Cleaning build cache..." -ForegroundColor Yellow
    if (Test-Path $CacheDir) {
        Remove-Item -Recurse -Force $CacheDir
    }
    docker builder prune -f
}

# Create cache directory
if (!(Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir | Out-Null
}

# Build command with cache options
$BuildArgs = @(
    "--progress=plain",
    "--build-arg", "BUILDKIT_INLINE_CACHE=1",
    "-t", "${ImageName}:${ImageTag}"
)

# Add cache options based on configuration
if ($RegistryCache -ne "") {
    Write-Host "📦 Using registry cache: $RegistryCache" -ForegroundColor Cyan
    $BuildArgs += @(
        "--cache-from", "type=registry,ref=$RegistryCache",
        "--cache-to", "type=registry,ref=$RegistryCache,mode=max"
    )
} else {
    Write-Host "💾 Using local cache directory: $CacheDir" -ForegroundColor Cyan
    $BuildArgs += @(
        "--cache-from", "type=local,src=$CacheDir",
        "--cache-to", "type=local,dest=$CacheDir,mode=max",
        "--cache-from", "${ImageName}:${ImageTag}"
    )
}

# Add verbose output if requested
if ($Verbose) {
    $BuildArgs += @("--no-cache-filter", "")
}

Write-Host "🔨 Building with cache optimizations..." -ForegroundColor Blue
Write-Host "Command: docker build $($BuildArgs -join ' ') ." -ForegroundColor Gray

# Execute build
try {
    & docker build @BuildArgs .
    
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    Write-Host "📊 Image information:" -ForegroundColor Cyan
    docker images "${ImageName}:${ImageTag}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Show cache usage
    Write-Host "💾 Cache directory size:" -ForegroundColor Cyan
    if (Test-Path $CacheDir) {
        $cacheSize = (Get-ChildItem -Recurse $CacheDir | Measure-Object -Property Length -Sum).Sum
        $cacheSizeMB = [math]::Round($cacheSize / 1MB, 2)
        Write-Host "  $cacheSizeMB MB"
    }
    
    Write-Host "🎉 Build optimization tips:" -ForegroundColor Green
    Write-Host "  - PyTorch wheels are cached and won't re-download on subsequent builds"
    Write-Host "  - APT packages are cached for faster system dependency installation"
    Write-Host "  - Use -Clean for a fresh build if you encounter issues"
    Write-Host "  - Use -RegistryCache for shared cache across machines/CI"
    
} catch {
    Write-Host "❌ Build failed: $_" -ForegroundColor Red
    exit 1
}
