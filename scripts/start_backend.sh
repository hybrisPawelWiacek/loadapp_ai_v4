#!/bin/bash

# Exit on error
set -e

# Directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

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

# Add the project root to PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

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

# Set Flask environment variables
export FLASK_APP=backend/app.py
export FLASK_ENV=${ENV:-development}
export FLASK_DEBUG=${DEBUG:-true}
export FLASK_RUN_PORT=${PORT:-5001}
export FLASK_RUN_HOST=${HOST:-localhost}

# Kill any existing Flask processes
echo "Checking for existing Flask processes..."
pkill -f "python.*backend/app.py" || true

# Start the Flask backend
echo "Starting Flask backend on port ${FLASK_RUN_PORT}..."
python -m flask run

# Deactivate virtual environment on exit
trap "deactivate" EXIT
