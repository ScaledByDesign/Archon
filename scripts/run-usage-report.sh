#!/bin/bash
# LiteLLM Usage Report Runner
# This script runs the usage monitor inside a Docker container with database access

# Default values
HOURS=24
FORMAT="text"
OUTPUT=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --hours)
            HOURS="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--hours HOURS] [--format FORMAT] [--output FILE]"
            echo "  --hours HOURS    Time period in hours (default: 24)"
            echo "  --format FORMAT  Output format: text or json (default: text)"
            echo "  --output FILE    Output file (default: stdout)"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Build the Docker command
DOCKER_CMD="docker run --rm --network zoi-network -v $(pwd)/scripts:/scripts python:3.11-slim bash -c \"
pip install psycopg2-binary > /dev/null 2>&1 && 
python /scripts/litellm-usage-monitor.py --host postgres --hours $HOURS --format $FORMAT"

# Add output redirection if specified
if [ ! -z "$OUTPUT" ]; then
    DOCKER_CMD="$DOCKER_CMD --output /scripts/$OUTPUT"
fi

DOCKER_CMD="$DOCKER_CMD\""

# Execute the command
echo "Generating LiteLLM usage report..."
eval $DOCKER_CMD

if [ ! -z "$OUTPUT" ]; then
    echo "Report saved to scripts/$OUTPUT"
fi
