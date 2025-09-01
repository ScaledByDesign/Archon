# Refact Agent Dockerfile
# Multi-stage build for optimized Rust binary

FROM rust:1.83-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    libsqlite3-dev \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Cargo files for dependency caching
COPY Cargo.toml ./
COPY build.rs ./

# Create dummy main.rs for dependency build
RUN mkdir src && echo "fn main() {}" > src/main.rs

# Build dependencies (this layer will be cached)
RUN cargo build --release && rm -rf src target/release/deps/refact*

# Copy source code
COPY src ./src
COPY assets ./assets
COPY examples ./examples
COPY tests ./tests

# Build the actual binary
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    libssl3 \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -r -s /bin/false -m -d /app refact

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/refact-lsp /usr/local/bin/refact-lsp

# Create necessary directories
RUN mkdir -p /app/.cache/refact /app/.config/refact && \
    chown -R refact:refact /app

# Configuration will be mounted at runtime

# Switch to app user
USER refact

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Default command
CMD ["refact-lsp", "--http-port", "8001", "--address-url", "/app/.config/refact/bring-your-own-key.yaml", "--logs-stderr", "--basic-telemetry"]
