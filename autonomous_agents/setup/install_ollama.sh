#!/bin/bash
set -e

echo "🚀 Installing Ollama..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📦 Detected Linux"

    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        echo "✅ Ollama is already installed"
        ollama --version
        exit 0
    fi

    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📦 Detected macOS"

    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        echo "✅ Ollama is already installed"
        ollama --version
        exit 0
    fi

    # Install via Homebrew if available
    if command -v brew &> /dev/null; then
        brew install ollama
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    echo "❌ Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "✅ Ollama installation complete!"
