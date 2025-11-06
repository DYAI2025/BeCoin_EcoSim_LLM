#!/bin/bash
set -e

echo "📥 Downloading AI models for autonomous agents..."

# Model to download
MODEL="qwen2.5-coder:7b"
BACKUP_MODEL="llama3.1:8b"  # Already installed, so using as backup

echo "🎯 Primary model: $MODEL"
echo "🔄 Backup model: $BACKUP_MODEL"

# Check available disk space
REQUIRED_SPACE=10  # GB
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo "❌ Insufficient disk space. Required: ${REQUIRED_SPACE}GB, Available: ${AVAILABLE_SPACE}GB"
    exit 1
fi

echo "✅ Sufficient disk space: ${AVAILABLE_SPACE}GB"

# Check if model is already downloaded
if ollama list | grep -q "$MODEL"; then
    echo "✅ $MODEL is already downloaded"
else
    echo "📦 Downloading $MODEL (this may take 5-10 minutes)..."

    if ollama pull "$MODEL"; then
        echo "✅ $MODEL downloaded successfully"
    else
        echo "⚠️  Primary model download failed, using backup model..."
        MODEL="$BACKUP_MODEL"
    fi
fi

# Save active model to config
mkdir -p ../config
cat > ../config/models.json <<EOF
{
  "primary_model": "$MODEL",
  "backup_model": "$BACKUP_MODEL",
  "endpoint": "http://localhost:11434",
  "options": {
    "temperature": 0.2,
    "num_ctx": 8192,
    "top_p": 0.9
  }
}
EOF

echo "✅ Model configuration saved to config/models.json"
echo ""
echo "🎉 Model setup complete!"
echo "Active model: $MODEL"
