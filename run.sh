#!/bin/bash

echo "Starting Home Repair Assistant..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file with your GOOGLE_API_KEY"
    echo "Example: GOOGLE_API_KEY=your_key_here"
    exit 1
fi

echo "Starting Streamlit application..."
streamlit run main.py
