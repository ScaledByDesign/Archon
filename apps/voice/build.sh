#!/bin/bash

# Enhanced Docker build script with comprehensive caching
set -e

# Configuration
IMAGE_NAME="realtime-voice-chat"
IMAGE_TAG="latest"
CACHE_DIR=".buildcache"
REGISTRY_CACHE=""  # Set to your registry for shared cache, e.g., "ghcr.io/yourorg/yourapp:buildcache"

# Parse command line arguments
CLEAN_BUILD=false
USE_REGISTRY_CACHE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --registry-cache)
            USE_REGISTRY_CACHE=true
            REGISTRY_CACHE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --clean              Clean build without cache"
            echo "  --registry-cache URL Use registry cache (e.g., ghcr.io/org/app:buildcache)"
            echo "  --verbose            Verbose output"
            echo "  -h, --help          Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 Starting optimized Docker build with comprehensive caching..."

# Enable BuildKit for faster builds and cache mounts
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Clean build cache if requested
if [ "$CLEAN_BUILD" = true ]; then
    echo "🧹 Cleaning build cache..."
    rm -rf "$CACHE_DIR"
    docker builder prune -f
fi

# Create cache directory
mkdir -p "$CACHE_DIR"

# Build command with cache options
BUILD_ARGS=(
    "--progress=plain"
    "--build-arg" "BUILDKIT_INLINE_CACHE=1"
    "-t" "${IMAGE_NAME}:${IMAGE_TAG}"
)

# Add cache options based on configuration
if [ "$USE_REGISTRY_CACHE" = true ] && [ -n "$REGISTRY_CACHE" ]; then
    echo "📦 Using registry cache: $REGISTRY_CACHE"
    BUILD_ARGS+=(
        "--cache-from" "type=registry,ref=$REGISTRY_CACHE"
        "--cache-to" "type=registry,ref=$REGISTRY_CACHE,mode=max"
    )
else
    echo "💾 Using local cache directory: $CACHE_DIR"
    BUILD_ARGS+=(
        "--cache-from" "type=local,src=$CACHE_DIR"
        "--cache-to" "type=local,dest=$CACHE_DIR,mode=max"
        "--cache-from" "${IMAGE_NAME}:${IMAGE_TAG}"
    )
fi

# Add verbose output if requested
if [ "$VERBOSE" = true ]; then
    BUILD_ARGS+=("--no-cache-filter" "")
fi

echo "🔨 Building with cache optimizations..."
echo "Command: docker build ${BUILD_ARGS[*]} ."

# Execute build
docker build "${BUILD_ARGS[@]}" .

echo "✅ Build completed successfully!"
echo "📊 Image information:"
docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Show cache usage
echo "💾 Cache directory size:"
if [ -d "$CACHE_DIR" ]; then
    du -sh "$CACHE_DIR" 2>/dev/null || echo "Cache directory not accessible"
fi

echo "🎉 Build optimization tips:"
echo "  - PyTorch wheels are cached and won't re-download on subsequent builds"
echo "  - APT packages are cached for faster system dependency installation"
echo "  - Use --clean for a fresh build if you encounter issues"
echo "  - Use --registry-cache for shared cache across machines/CI"
