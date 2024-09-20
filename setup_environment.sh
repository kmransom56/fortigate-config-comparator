#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

ENV_NAME="network_project"
ENV_PATH="$HOME/Documents/network_project/.venvs/$ENV_NAME"

echo "Checking for Python3..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 could not be found. Please install Python 3."
    exit 1
fi

echo "Python3 found. Version:"
python3 --version

echo "Checking for venv module..."
if ! python3 -c "import venv" &> /dev/null; then
    echo "Python venv module not found. Please install python3-venv."
    exit 1
fi

echo "Creating virtual environment at: $ENV_PATH"
python3 -m venv "$ENV_PATH"

if [ ! -f "$ENV_PATH/bin/activate" ]; then
    echo "Failed to create virtual environment. Activation script not found."
    exit 1
fi

echo "Activating environment: $ENV_NAME"
source "$ENV_PATH/bin/activate"

if [ "$VIRTUAL_ENV" != "$ENV_PATH" ]; then
    echo "Failed to activate virtual environment. Exiting."
    exit 1
fi

echo "Virtual environment activated successfully."

echo "Upgrading pip..."
python -m pip install --upgrade pip
echo "Creating requirements.txt file..."
cat << EOF > requirements.txt
autogen
pyautogen
openpyxl
openai
scikit-learn
flaml[automl]
chromadb
EOF

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

#echo "Installing dependencies..."
#pip install autogen pyautogen openpyxl openai scikit-learn flaml[automl] chromadb

echo "Updating requirements.txt..."
pip freeze > requirements.txt

echo "Environment setup complete. To activate, use: source $ENV_PATH/bin/activate"
#
echo "Running skills.py..."
python ~/Documents/network_project/skills.py
