#!/bin/bash

# Setup Development Environment for FastAPI RAG System
# Creates virtual environment and installs dependencies

set -e

echo "🔧 Setting up Development Environment for FastAPI RAG System"
echo "=" * 60

# Check Python version
python_version=$(python3 --version 2>/dev/null || echo "Python not found")
echo "📋 Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "   Please install Python 3.8+ and try again"
    exit 1
fi

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
    read -p "   Do you want to recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "   Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
echo "   Installing from requirements.txt..."
pip install -r requirements.txt

# Verify installation
echo ""
echo "✅ Verifying installation..."
python -c "
import fastapi
import uvicorn
import hvac
import qdrant_client
print('✅ FastAPI:', fastapi.__version__)
print('✅ Uvicorn: Available')
print('✅ HVAC (Vault):', hvac.__version__)
print('✅ Qdrant Client:', qdrant_client.__version__)
"

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 To activate the environment:"
echo "   source venv/bin/activate"
echo ""
echo "🚀 To start the FastAPI server:"
echo "   cd src && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🔗 API will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/health"
echo ""
echo "🧪 To run tests:"
echo "   ./scripts/test-fastapi-integration.sh"
