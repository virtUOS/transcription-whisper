#!/bin/sh

set -e

# Keep package yt-dlp updated on container start up
pip install --upgrade --no-cache-dir yt-dlp

# Run with streamlit user for security
runuser -u streamlituser -- streamlit run app.py --server.port=8501 --server.address=0.0.0.0 "$@"
