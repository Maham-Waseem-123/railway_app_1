#!/bin/bash

# Activate the virtual environment
source /antenv/bin/activate

# Install any missing dependencies
pip install -r requirements.txt

# Run migrations if needed
flask db upgrade

# Start Gunicorn
gunicorn --bind=0.0.0.0:${PORT:-8000} --timeout 600 app:app
