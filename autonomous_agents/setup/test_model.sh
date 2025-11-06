#!/bin/bash
set -e

echo "🧪 Testing AI model..."

# Load config
CONFIG_FILE="../config/models.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found. Run download_models.sh first."
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not installed, using default model"
    MODEL="llama3.1:8b"
else
    MODEL=$(jq -r '.primary_model' "$CONFIG_FILE")
fi

echo "🎯 Testing model: $MODEL"

# Test prompt
TEST_PROMPT="Write a Python function that returns 'Hello, World!'"

echo ""
echo "📝 Test prompt: $TEST_PROMPT"
echo ""
echo "🤖 Model response:"
echo "---"

# Call Ollama API
RESPONSE=$(curl -s http://localhost:11434/api/generate -d "{
  \"model\": \"$MODEL\",
  \"prompt\": \"$TEST_PROMPT\",
  \"stream\": false
}" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//' | sed 's/\\n/\n/g')

echo "$RESPONSE"
echo "---"
echo ""

# Verify response contains code
if echo "$RESPONSE" | grep -q "def\|return\|Hello"; then
    echo "✅ Model test passed! Model is generating code correctly."
else
    echo "⚠️  Model response doesn't look like code. Check model installation."
fi
