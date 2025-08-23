#!/bin/bash

# MCP Integration Setup Script for RealtimeVoiceChat
# This script automates the installation and configuration of MCP tools

set -e  # Exit on any error

echo "🚀 Setting up MCP Integration for RealtimeVoiceChat..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_nodejs() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js is installed: $NODE_VERSION"
        
        if command -v npm &> /dev/null; then
            NPM_VERSION=$(npm --version)
            print_success "npm is installed: $NPM_VERSION"
        else
            print_error "npm is not installed. Please install npm."
            exit 1
        fi
    else
        print_error "Node.js is not installed. Please install Node.js first."
        print_status "Visit: https://nodejs.org/"
        exit 1
    fi
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version)
        print_success "Python is installed: $PYTHON_VERSION"
        
        # Check Python version (should be < 3.13 for RealtimeVoiceChat)
        PYTHON_MAJOR=$(python -c "import sys; print(sys.version_info.major)")
        PYTHON_MINOR=$(python -c "import sys; print(sys.version_info.minor)")
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
            print_warning "Python 3.13+ detected. RealtimeVoiceChat may have compatibility issues."
            print_warning "Consider using Python 3.9-3.12 for best compatibility."
        fi
    else
        print_error "Python is not installed. Please install Python first."
        exit 1
    fi
}

# Install MCP servers
install_mcp_servers() {
    print_status "Installing MCP servers..."
    
    # Install filesystem server
    print_status "Installing MCP filesystem server..."
    if npm install -g @modelcontextprotocol/server-filesystem; then
        print_success "MCP filesystem server installed successfully"
    else
        print_error "Failed to install MCP filesystem server"
        exit 1
    fi
    
    # Verify installation
    if command -v mcp-server-filesystem &> /dev/null; then
        print_success "MCP filesystem server is accessible"
    else
        print_warning "MCP filesystem server may not be in PATH"
        print_status "Try adding npm global bin to PATH: export PATH=\$PATH:\$(npm config get prefix)/bin"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        print_status "Installing from requirements.txt..."
        if pip install -r requirements.txt; then
            print_success "Python dependencies installed successfully"
        else
            print_error "Failed to install Python dependencies"
            exit 1
        fi
    else
        print_warning "requirements.txt not found. Installing core dependencies..."
        pip install mcp fastapi uvicorn python-dotenv ollama openai numpy scipy
    fi
}

# Test MCP integration
test_mcp_integration() {
    print_status "Testing MCP integration..."
    
    if [ -f "test_mcp.py" ]; then
        print_status "Running MCP integration tests..."
        if python test_mcp.py; then
            print_success "MCP integration tests passed!"
        else
            print_error "MCP integration tests failed"
            exit 1
        fi
    else
        print_warning "test_mcp.py not found. Skipping integration tests."
    fi
}

# Create configuration files
create_config() {
    print_status "Creating configuration files..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# MCP Configuration
MCP_WORKSPACE_PATH=$(pwd)
LOG_LEVEL=INFO

# Ollama Configuration
OLLAMA_BASE_URL=http://127.0.0.1:11434

# Optional: OpenAI API Key
# OPENAI_API_KEY=your_api_key_here
EOF
        print_success "Created .env file"
    else
        print_status ".env file already exists"
    fi
}

# Main setup function
main() {
    echo "🎯 MCP Integration Setup for RealtimeVoiceChat"
    echo "=============================================="
    
    # Check prerequisites
    check_nodejs
    check_python
    
    # Install components
    install_mcp_servers
    install_python_deps
    
    # Create configuration
    create_config
    
    # Test integration
    test_mcp_integration
    
    echo ""
    echo "🎉 MCP Integration setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review the configuration in .env file"
    echo "2. Start the RealtimeVoiceChat server: python code/server.py"
    echo "3. Open http://localhost:8000 in your browser"
    echo "4. Try voice commands like 'List the files in the current directory'"
    echo ""
    echo "For more information, see MCP_INTEGRATION.md"
}

# Run main function
main "$@"
