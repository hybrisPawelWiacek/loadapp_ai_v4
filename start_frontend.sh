#!/bin/bash

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Parse command line arguments
check_requirements=false
while getopts "r" opt; do
    case $opt in
        r) check_requirements=true ;;
        \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    esac
done

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    check_requirements=true
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check requirements only if -r flag is provided or venv was just created
if [ "$check_requirements" = true ] && [ -f "requirements.txt" ]; then
    echo "Installing/updating requirements..."
    pip install -r requirements.txt
fi

# Add the project root to PYTHONPATH
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Loading environment from .env file..."
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found, using default configuration"
    # Copy template if it exists and .env doesn't
    if [ -f "$SCRIPT_DIR/template.env" ]; then
        echo "Creating .env from template..."
        cp "$SCRIPT_DIR/template.env" "$SCRIPT_DIR/.env"
        echo "Please edit .env file and set your configuration values"
        exit 1
    fi
fi

# Kill any existing Streamlit processes
echo "Checking for existing Streamlit processes..."
pkill -f "streamlit.*frontend/streamlit_app.py" || true

# Start the Streamlit app
echo "Starting LoadApp.AI frontend on port ${FRONTEND_PORT:-8501}..."
cd "$SCRIPT_DIR"
streamlit run frontend/streamlit_app.py \
    --server.port=${FRONTEND_PORT:-8501} \
    --server.address=${BACKEND_HOST:-localhost} \
    --logger.level=${LOG_LEVEL:-INFO}

# Deactivate virtual environment on exit
trap "deactivate" EXIT
