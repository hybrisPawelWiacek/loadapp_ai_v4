#!/bin/bash

# Exit on error
set -e

# Directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Parse command line arguments
CHECK_REQUIREMENTS=false
while getopts "r" opt; do
    case $opt in
        r)
            CHECK_REQUIREMENTS=true
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            exit 1
            ;;
    esac
done

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Error: Virtual environment not found in $PROJECT_ROOT/venv"
    echo "Please create a virtual environment first using:"
    echo "python3 -m venv venv"
    echo "And install dependencies using:"
    echo "source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Check and install requirements if -r flag is used
if [ "$CHECK_REQUIREMENTS" = true ]; then
    echo "Checking and updating requirements..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
fi

# Add the project root to PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

# Create cache directory if it doesn't exist
CACHE_DIR="$PROJECT_ROOT/cache"
mkdir -p "$CACHE_DIR"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment from .env file..."
    # Only export valid environment variables (ignore comments and empty lines)
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        # Remove any leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        # Only export if key is not empty
        if [[ ! -z $key ]]; then
            export "$key=$value"
        fi
    done < "$PROJECT_ROOT/.env"
else
    echo "Warning: .env file not found, using default configuration"
    # Copy template if it exists and .env doesn't
    if [ -f "$PROJECT_ROOT/template.env" ]; then
        echo "Creating .env from template..."
        cp "$PROJECT_ROOT/template.env" "$PROJECT_ROOT/.env"
        echo "Please edit .env file and set your configuration values"
        exit 1
    fi
fi

# Check for required Python packages
echo "Checking required packages..."
python3 -c "import streamlit, folium, plotly, pandas" 2>/dev/null || {
    echo "Error: Missing required Python packages"
    echo "Please run: pip install -r requirements.txt"
    exit 1
}

# Kill any existing Streamlit processes
echo "Checking for existing Streamlit processes..."
pkill -f "streamlit run" || true

# Start Streamlit frontend with the new implementation
echo "Starting Streamlit frontend on port ${FRONTEND_PORT:-8501}..."
cd "$PROJECT_ROOT"
streamlit run frontend/app_main.py --server.port=${FRONTEND_PORT:-8501} || {
    echo "Error: Failed to start Streamlit frontend"
    echo "Please check the logs above for more details"
    exit 1
}

# Deactivate virtual environment on exit
trap "deactivate" EXIT
