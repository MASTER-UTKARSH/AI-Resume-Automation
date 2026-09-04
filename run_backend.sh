#!/usr/bin/env bash
# Launcher script for AI-Powered Resume Automation Backend & Dashboard
set -e

echo "Starting AI-Powered Resume Automation Backend..."
echo "Documentation will be available at: http://127.0.0.1:8000/docs"
echo "Clyde Dashboard available at:       http://127.0.0.1:8000/dashboard/clyde_jobs/code.html"

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
