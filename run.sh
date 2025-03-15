#!/bin/bash
# Run script for Unix-based systems (Mac, Linux)

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the application
python src/main.py 