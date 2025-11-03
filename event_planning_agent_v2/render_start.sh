#!/bin/bash
# Render startup script for Event Planning Agent v2

# Set Python path to include current directory
export PYTHONPATH="${PYTHONPATH}:/opt/render/project/src"

# Run uvicorn with the correct module path
cd /opt/render/project/src
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
