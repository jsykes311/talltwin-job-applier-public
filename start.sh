#!/bin/bash
PORT="${PORT:-8501}"
echo "Starting Public Streamlit App on port $PORT..."
streamlit run web/app.py --server.port="$PORT" --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false
