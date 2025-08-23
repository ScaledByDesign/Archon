# Zoi Voice Chat - Centralized Model Management

## Overview

The Zoi Voice Chat system now uses a centralized model directory approach that provides several key benefits:

- **Shared Models**: All Zoi ecosystem services share the same model directory
- **No Duplicates**: Eliminates duplicate model downloads across services
- **Faster Builds**: Models are downloaded at runtime, not during Docker build
- **Easy Management**: Single location for all AI models
- **Configurable**: Easily change model storage location via environment variables

## Model Directory Structure

```
D:/models/                          # Base directory (configurable)
├── huggingface/                    # HuggingFace models
│   ├── hub/                        # Model files
│   └── transformers/               # Transformers cache
├── torch/                          # PyTorch models
│   └── hub/                        # Torch Hub models (Silero VAD, etc.)
├── whisper/                        # Whisper models
├── coqui-tts/                      # Coqui TTS models
└── ollama/                         # Ollama models
```

## Configuration

### Environment Variables

All model paths are configurable via the `.env` file:

```bash
# Model Storage Configuration
MODELS_BASE_DIR=D:/models           # Change this to your preferred location
HF_CACHE_SUBDIR=huggingface
TORCH_CACHE_SUBDIR=torch
WHISPER_CACHE_SUBDIR=whisper
COQUI_TTS_CACHE_SUBDIR=coqui-tts
OLLAMA_CACHE_SUBDIR=ollama
```

### Fallback Values

If environment variables are not set, the system uses these defaults:
- Base directory: `D:/models`
- Subdirectories: `huggingface`, `torch`, `whisper`, `coqui-tts`, `ollama`

## Setup Instructions

### 1. Quick Setup

Run the setup script to create the directory structure:

```bash
./setup-models.sh
```

### 2. Manual Setup

Create the directories manually:

```bash
mkdir -p D:/models/{huggingface,torch,whisper,coqui-tts,ollama}
mkdir -p D:/models/huggingface/{hub,transformers}
mkdir -p D:/models/torch/hub
```

### 3. Custom Location

To use a different model directory:

1. Edit `.env` file:
   ```bash
   MODELS_BASE_DIR=/your/custom/path
   ```

2. Create the directory structure:
   ```bash
   ./setup-models.sh
   ```

## Model Downloads

Models are automatically downloaded on first run:

1. **Silero VAD**: Voice Activity Detection model
2. **Whisper**: Speech-to-text model (configurable via `WHISPER_MODEL`)
3. **Sentence Classifier**: Text processing model
4. **Coqui TTS**: Text-to-speech models (downloaded as needed)

## Benefits

### For Development
- Faster Docker builds (no model downloads during build)
- Consistent model versions across services
- Easy model management and updates

### For Production
- Reduced storage requirements
- Faster service startup (models already cached)
- Centralized model versioning

### For the Zoi Ecosystem
- Shared models across all services
- No duplicate downloads
- Consistent model management

## Troubleshooting

### Permission Issues
If you encounter permission issues:

```bash
# Fix ownership (Linux/Mac)
sudo chown -R $USER:$USER /path/to/models

# Fix permissions
chmod -R 755 /path/to/models
```

### Disk Space
Monitor disk usage as models can be large:

```bash
# Check model directory size
du -sh D:/models

# Check individual subdirectories
du -sh D:/models/*
```

### Model Updates
To update models, simply delete the cached files:

```bash
# Remove specific model cache
rm -rf D:/models/huggingface/hub/models--*model-name*

# Or remove all cached models (they'll re-download)
rm -rf D:/models/*/
```

## Integration with Other Zoi Services

Other Zoi services can use the same model directory by:

1. Setting the same environment variables
2. Mounting the same host directory
3. Using the same model cache paths

Example for another service:
```yaml
volumes:
  - ${MODELS_BASE_DIR:-D:/models}:/models
environment:
  - HF_HOME=/models/${HF_CACHE_SUBDIR:-huggingface}
  - TORCH_HOME=/models/${TORCH_CACHE_SUBDIR:-torch}
```

This ensures all Zoi services share the same models efficiently!
