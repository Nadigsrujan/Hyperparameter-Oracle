#!/bin/bash
echo "================================================"
echo "  Hyperparameter Oracle - DSA-Driven AutoML"
echo "================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH"
    echo "Please install Python 3.8+ using Homebrew or from https://www.python.org/"
    exit 1
fi

echo "[1/4] Checking Python dependencies..."
if python3 -c "import flask, numpy, sklearn" &> /dev/null; then
    echo "Dependencies already installed"
else
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "[2/4] Checking C library..."
# Ensure build directory exists
mkdir -p build

if [ -f "build/oracle.dll" ]; then
    echo "C library found: build/oracle.dll"
else
    echo "[WARNING] C library not found"
    echo "Attempting to compile..."
    gcc -shared -o build/oracle.dll -fPIC src/c/*.c -Iinclude
    if [ $? -eq 0 ]; then
        echo "✓ Compilation successful"
    else
        echo "[ERROR] Compilation failed. Please ensure gcc is installed."
        exit 1
    fi
fi

echo ""
echo "[3/4] Starting Flask API Server..."
# Using python3 to run the server in the source directory
cd src/python
python3 api_server.py &
API_PID=$!

echo ""
echo "[4/4] Waiting for server to start..."
sleep 3

echo ""
echo "================================================"
echo "  Server Started Successfully! (PID: $API_PID)"
echo "================================================"
echo ""
echo "Dashboard URL: http://localhost:5001"
echo ""

# On macOS, open the browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5001
fi

echo "Press Ctrl+C to stop the server..."

# Wait for the background process
trap "kill $API_PID; echo -e '\nStopping server...'; exit" INT
wait $API_PID
