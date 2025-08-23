#!/bin/bash

# Test script to demonstrate Docker caching effectiveness
set -e

echo "🧪 Docker Caching Test Script"
echo "This script demonstrates the effectiveness of Docker caching by timing builds"
echo ""

# Configuration
IMAGE_NAME="realtime-voice-chat"
IMAGE_TAG="cache-test"

# Function to time a build
time_build() {
    local description="$1"
    local build_args="$2"
    
    echo "⏱️  Testing: $description"
    echo "Command: docker build $build_args -t ${IMAGE_NAME}:${IMAGE_TAG} ."
    echo ""
    
    start_time=$(date +%s)
    
    # Run the build
    eval "docker build $build_args -t ${IMAGE_NAME}:${IMAGE_TAG} . > build.log 2>&1"
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo "✅ Completed in ${duration} seconds"
    echo ""
    
    # Show some stats from the build log
    if grep -q "CACHED" build.log; then
        cached_layers=$(grep -c "CACHED" build.log)
        echo "📊 Cached layers: $cached_layers"
    fi
    
    if grep -q "downloading" build.log; then
        echo "📥 Downloads detected in build log"
    else
        echo "🚀 No downloads detected - using cache!"
    fi
    
    echo "----------------------------------------"
    echo ""
}

# Enable BuildKit
export DOCKER_BUILDKIT=1

echo "🧹 Cleaning up any existing test images..."
docker rmi ${IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null || true

echo "🗑️  Cleaning build cache for accurate test..."
rm -rf .buildcache
docker builder prune -f > /dev/null 2>&1

echo ""
echo "Starting cache effectiveness tests..."
echo "========================================"
echo ""

# Test 1: First build (no cache)
time_build "First build (no cache)" "--progress=plain"

# Test 2: Second build (should use layer cache)
time_build "Second build (layer cache)" "--progress=plain"

# Test 3: Build with cache mounts
time_build "Build with cache mounts" "--progress=plain --cache-from type=local,src=.buildcache --cache-to type=local,dest=.buildcache,mode=max"

# Test 4: Another build with cache mounts (should be very fast)
time_build "Another build with cache mounts" "--progress=plain --cache-from type=local,src=.buildcache --cache-to type=local,dest=.buildcache,mode=max"

# Show cache directory size
echo "💾 Cache directory analysis:"
if [ -d ".buildcache" ]; then
    cache_size=$(du -sh .buildcache | cut -f1)
    echo "Build cache size: $cache_size"
    echo "Cache contents:"
    ls -la .buildcache/ 2>/dev/null || echo "Cache directory structure not accessible"
else
    echo "No build cache directory found"
fi

echo ""
echo "🎉 Cache test completed!"
echo ""
echo "💡 Key takeaways:"
echo "  - First build downloads everything (PyTorch ~1.1GB)"
echo "  - Subsequent builds reuse cached layers and packages"
echo "  - Cache mounts provide the best performance for pip packages"
echo "  - Layer cache helps with unchanged Dockerfile instructions"
echo ""
echo "🧹 Cleanup:"
echo "  - Remove test image: docker rmi ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  - Remove build cache: rm -rf .buildcache"
echo "  - Remove build log: rm build.log"

# Cleanup
rm -f build.log
