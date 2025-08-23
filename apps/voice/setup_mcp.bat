@echo off
REM MCP Integration Setup Script for RealtimeVoiceChat (Windows)
REM This script automates the installation and configuration of MCP tools

setlocal enabledelayedexpansion

echo 🚀 Setting up MCP Integration for RealtimeVoiceChat...
echo.

REM Check if Node.js is installed
echo [INFO] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js first.
    echo [INFO] Visit: https://nodejs.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo [SUCCESS] Node.js is installed: !NODE_VERSION!
)

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed. Please install npm.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    echo [SUCCESS] npm is installed: !NPM_VERSION!
)

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python first.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [SUCCESS] Python is installed: !PYTHON_VERSION!
)

REM Install MCP servers
echo [INFO] Installing MCP servers...
echo [INFO] Installing MCP filesystem server...
call npm install -g @modelcontextprotocol/server-filesystem
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install MCP filesystem server
    pause
    exit /b 1
) else (
    echo [SUCCESS] MCP filesystem server installed successfully
)

REM Verify MCP server installation
where mcp-server-filesystem >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] MCP filesystem server may not be in PATH
    echo [INFO] You may need to add npm global bin to PATH
) else (
    echo [SUCCESS] MCP filesystem server is accessible
)

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
if exist requirements.txt (
    echo [INFO] Installing from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python dependencies
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] Python dependencies installed successfully
    )
) else (
    echo [WARNING] requirements.txt not found. Installing core dependencies...
    pip install mcp fastapi uvicorn python-dotenv ollama openai numpy scipy
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo [INFO] Creating .env file...
    (
        echo # MCP Configuration
        echo MCP_WORKSPACE_PATH=%CD%
        echo LOG_LEVEL=INFO
        echo.
        echo # Ollama Configuration
        echo OLLAMA_BASE_URL=http://127.0.0.1:11434
        echo.
        echo # Optional: OpenAI API Key
        echo # OPENAI_API_KEY=your_api_key_here
    ) > .env
    echo [SUCCESS] Created .env file
) else (
    echo [INFO] .env file already exists
)

REM Test MCP integration
if exist test_mcp.py (
    echo [INFO] Running MCP integration tests...
    python test_mcp.py
    if %errorlevel% neq 0 (
        echo [ERROR] MCP integration tests failed
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] MCP integration tests passed!
    )
) else (
    echo [WARNING] test_mcp.py not found. Skipping integration tests.
)

echo.
echo 🎉 MCP Integration setup completed successfully!
echo.
echo Next steps:
echo 1. Review the configuration in .env file
echo 2. Start the RealtimeVoiceChat server: python code/server.py
echo 3. Open http://localhost:8000 in your browser
echo 4. Try voice commands like 'List the files in the current directory'
echo.
echo For more information, see MCP_INTEGRATION.md
echo.
pause
