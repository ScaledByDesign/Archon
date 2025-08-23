#!/usr/bin/env python3
"""
Model Initializer - Downloads and caches models on first run
This reduces Docker build time by moving model downloads to runtime
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_silero_vad():
    """Download Silero VAD model if not already cached"""
    try:
        import torch
        # Use centralized model directory with fallback
        cache_dir = os.getenv('TORCH_HOME', '/models/torch')
        os.environ['TORCH_HOME'] = cache_dir

        # Check if model is already cached
        model_path = Path(cache_dir) / "hub" / "snakers4_silero-vad_master"
        if model_path.exists():
            logger.info("Silero VAD model already cached")
            return True

        logger.info("Downloading Silero VAD model...")
        torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        logger.info("Silero VAD model downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download Silero VAD model: {e}")
        return False

def ensure_whisper_model():
    """Download Whisper model if not already cached"""
    try:
        import faster_whisper
        model_name = os.getenv('WHISPER_MODEL', 'base.en')

        # Use centralized model directory with fallback
        whisper_cache_dir = os.getenv('WHISPER_CACHE_DIR', '/models/whisper')
        hf_cache_dir = os.getenv('HF_HOME', '/models/huggingface')

        # Set environment variables for model caching
        os.environ['WHISPER_CACHE_DIR'] = whisper_cache_dir
        os.environ['HF_HOME'] = hf_cache_dir

        # Check if model is already cached
        cache_dir = Path(hf_cache_dir) / "hub"
        model_cache_pattern = f"models--Systran--faster-whisper-{model_name}"

        if any(cache_dir.glob(f"*{model_cache_pattern}*")):
            logger.info(f"Whisper model '{model_name}' already cached")
            return True

        logger.info(f"Downloading Whisper model: {model_name}")
        model = faster_whisper.WhisperModel(model_name, device='cpu')
        logger.info(f"Whisper model '{model_name}' downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download Whisper model: {e}")
        return False

def ensure_sentence_classifier():
    """Download sentence classification model if not already cached"""
    try:
        from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
        model_name = 'KoljaB/SentenceFinishedClassification'

        # Use centralized model directory with fallback
        hf_cache_dir = os.getenv('HF_HOME', '/models/huggingface')
        transformers_cache_dir = os.getenv('TRANSFORMERS_CACHE', f'{hf_cache_dir}/transformers')

        # Set environment variables for model caching
        os.environ['HF_HOME'] = hf_cache_dir
        os.environ['TRANSFORMERS_CACHE'] = transformers_cache_dir

        # Check if model is already cached
        cache_dir = Path(hf_cache_dir) / "hub"
        model_cache_pattern = "models--KoljaB--SentenceFinishedClassification"

        if any(cache_dir.glob(f"*{model_cache_pattern}*")):
            logger.info("Sentence classification model already cached")
            return True

        logger.info("Downloading sentence classification model...")
        tokenizer = DistilBertTokenizerFast.from_pretrained(model_name)
        model = DistilBertForSequenceClassification.from_pretrained(model_name)
        logger.info("Sentence classification model downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download sentence classification model: {e}")
        return False

def initialize_models():
    """Initialize all required models"""
    logger.info("Starting model initialization...")
    
    success = True
    success &= ensure_silero_vad()
    success &= ensure_whisper_model()
    success &= ensure_sentence_classifier()
    
    if success:
        logger.info("All models initialized successfully")
        return True
    else:
        logger.error("Some models failed to initialize")
        return False

if __name__ == "__main__":
    if not initialize_models():
        sys.exit(1)
