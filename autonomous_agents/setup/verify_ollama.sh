#!/bin/bash
set -e

echo "🔍 Verifying Ollama installation..."

# Check if ollama command exists
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed or not in PATH"
    exit 1
fi

echo "✅ Ollama command found"
ollama --version

# Check if Ollama service is running
echo "🔍 Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama service is running"
else
    echo "⚠️  Ollama service is not running. Starting..."

    # Start Ollama service in background
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        systemctl --user start ollama 2>/dev/null || ollama serve &
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        ollama serve &
    fi

    # Wait for service to start
    echo "⏳ Waiting for Ollama service to start..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama service started successfully"
            break
        fi
        sleep 1
    done
fi

# List installed models
echo ""
echo "📦 Installed models:"
ollama list

echo ""
echo "✅ Ollama verification complete!"
