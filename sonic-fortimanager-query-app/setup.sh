#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create .env file from .env.example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit the .env file with your FortiManager details."
fi

# Run the application
python app.py