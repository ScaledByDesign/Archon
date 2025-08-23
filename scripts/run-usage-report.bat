@echo off
REM LiteLLM Usage Report Runner for Windows
REM This script runs the usage monitor inside a Docker container with database access

set HOURS=24
set FORMAT=text
set OUTPUT=

:parse_args
if "%1"=="--hours" (
    set HOURS=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--format" (
    set FORMAT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--output" (
    set OUTPUT=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--help" (
    echo Usage: %0 [--hours HOURS] [--format FORMAT] [--output FILE]
    echo   --hours HOURS    Time period in hours (default: 24)
    echo   --format FORMAT  Output format: text or json (default: text)
    echo   --output FILE    Output file (default: stdout)
    exit /b 0
)
if not "%1"=="" (
    echo Unknown option %1
    exit /b 1
)

echo Generating LiteLLM usage report...

if "%OUTPUT%"=="" (
    docker run --rm --network zoi-network -v "%cd%/scripts:/scripts" python:3.11-slim bash -c "pip install psycopg2-binary > /dev/null 2>&1 && python /scripts/litellm-usage-monitor.py --host postgres --hours %HOURS% --format %FORMAT%"
) else (
    docker run --rm --network zoi-network -v "%cd%/scripts:/scripts" python:3.11-slim bash -c "pip install psycopg2-binary > /dev/null 2>&1 && python /scripts/litellm-usage-monitor.py --host postgres --hours %HOURS% --format %FORMAT% --output /scripts/%OUTPUT%"
    echo Report saved to scripts/%OUTPUT%
)
