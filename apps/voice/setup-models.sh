#!/bin/bash

# Zoi Voice Chat - Model Directory Setup Script
# ==============================================
# This script creates the centralized model directory structure
# and optionally pre-downloads models to speed up first run.

set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading configuration from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set defaults if not provided by .env
MODELS_BASE_DIR=${MODELS_BASE_DIR:-"D:/models"}
HF_CACHE_SUBDIR=${HF_CACHE_SUBDIR:-"huggingface"}
TORCH_CACHE_SUBDIR=${TORCH_CACHE_SUBDIR:-"torch"}
WHISPER_CACHE_SUBDIR=${WHISPER_CACHE_SUBDIR:-"whisper"}
COQUI_TTS_CACHE_SUBDIR=${COQUI_TTS_CACHE_SUBDIR:-"coqui-tts"}
OLLAMA_CACHE_SUBDIR=${OLLAMA_CACHE_SUBDIR:-"ollama"}

echo "Setting up Zoi model directories..."
echo "Base directory: $MODELS_BASE_DIR"

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$MODELS_BASE_DIR/$HF_CACHE_SUBDIR"
mkdir -p "$MODELS_BASE_DIR/$TORCH_CACHE_SUBDIR"
mkdir -p "$MODELS_BASE_DIR/$WHISPER_CACHE_SUBDIR"
mkdir -p "$MODELS_BASE_DIR/$COQUI_TTS_CACHE_SUBDIR"
mkdir -p "$MODELS_BASE_DIR/$OLLAMA_CACHE_SUBDIR"

# Create subdirectories for HuggingFace
mkdir -p "$MODELS_BASE_DIR/$HF_CACHE_SUBDIR/hub"
mkdir -p "$MODELS_BASE_DIR/$HF_CACHE_SUBDIR/transformers"

# Create subdirectories for Torch
mkdir -p "$MODELS_BASE_DIR/$TORCH_CACHE_SUBDIR/hub"

echo "Directory structure created successfully!"

# Display the structure
echo ""
echo "Model directory structure:"
echo "├── $MODELS_BASE_DIR/"
echo "│   ├── $HF_CACHE_SUBDIR/ (HuggingFace models)"
echo "│   ├── $TORCH_CACHE_SUBDIR/ (PyTorch models)"
echo "│   ├── $WHISPER_CACHE_SUBDIR/ (Whisper models)"
echo "│   ├── $COQUI_TTS_CACHE_SUBDIR/ (Coqui TTS models)"
echo "│   └── $OLLAMA_CACHE_SUBDIR/ (Ollama models)"

echo ""
echo "Setup complete! You can now run 'docker-compose up' to start the voice chat service."
echo "Models will be downloaded automatically on first run and stored in the centralized directory."

# Optional: Ask if user wants to pre-download models
echo ""
read -p "Would you like to pre-download models now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pre-downloading models would require Python environment setup."
    echo "For now, models will be downloaded on first container run."
    echo "This ensures compatibility and proper environment setup."
fi

echo ""
echo "Note: All Zoi ecosystem services will now share these model directories,"
echo "eliminating duplicate downloads and saving disk space!"
