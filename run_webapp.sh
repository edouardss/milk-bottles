#!/bin/bash

# Script to run the Flask webapp with the virtual environment from parent directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Path to virtual environment in parent directory
VENV_PATH="$SCRIPT_DIR/../venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create a virtual environment in the parent directory first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment from $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Check if activation was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

# Change to the script directory
cd "$SCRIPT_DIR"

# Install/update requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# Run the Flask app
echo "Starting Flask webapp at http://localhost:5050"
python app.py
