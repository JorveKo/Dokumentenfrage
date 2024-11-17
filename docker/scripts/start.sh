#!/bin/bash
echo "Starting Neural Document Acquisition System..."
# Added --reload-exclude to ignore certain paths and prevent double reloading
uvicorn app.__init__:app --host 0.0.0.0 --port 5000 --reload --reload-exclude="logs/*" --reload-exclude="downloads/*"