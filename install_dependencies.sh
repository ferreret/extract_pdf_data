#!/bin/bash

echo "Installing dependencies for PDF data extraction project..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs
echo "Created logs directory"

# Create input directory if it doesn't exist
mkdir -p input
echo "Created input directory for PDF files"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "Installation completed!"
echo ""
echo "Before running the application, please:"
echo "1. Copy your .env file and set the required environment variables:"
echo "   - GENAI_API_KEY: Your Google GenAI API key"
echo "   - REQUESTY_API_KEY: Your Requesty API key (if using Requesty)"
echo "   - REQUESTY_BASE_URL: Your Requesty API base URL (if using Requesty)"
echo ""
echo "2. Place your PDF files in the 'input' directory"
echo ""
echo "3. Run the application with: python3 main.py"