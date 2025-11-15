#!/bin/bash
# Setup script for Raspberry Pi 5 deployment
# Orange Burkina Faso RAG Chatbot

set -e  # Exit on error

echo "🚀 Orange RAG - Installation pour Raspberry Pi 5"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on ARM64
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    echo -e "${YELLOW}⚠️  Warning: This script is optimized for ARM64 (Pi 5), detected: $ARCH${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check RAM
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 7 ]; then
    echo -e "${RED}❌ Error: This setup requires at least 8GB RAM, detected: ${TOTAL_RAM}GB${NC}"
    exit 1
fi

echo -e "${GREEN}✅ System check passed${NC}"
echo ""

# Step 1: Update system
echo "📦 Step 1/6: Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv cmake build-essential curl wget htop

# Step 2: Create virtual environment
echo "📦 Step 2/6: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Step 3: Install Python dependencies
echo "📦 Step 3/6: Installing Python packages (this may take 10-15 minutes)..."
pip install --upgrade pip

# Install llama-cpp-python optimized for CPU
echo "   Installing llama-cpp-python..."
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python

# Install other dependencies
echo "   Installing other dependencies..."
pip install fastapi uvicorn[standard] pydantic
pip install sentence-transformers faiss-cpu
pip install numpy psutil

# Step 4: Choose and download model
echo ""
echo "📦 Step 4/6: Choosing model..."
echo ""
echo "Select a model to download:"
echo "1) Phi-3-Mini Q4 (2.3GB) - RECOMMENDED - Best quality"
echo "2) TinyLlama Q4 (0.6GB) - Fastest, lower quality"
echo "3) Llama-3.2-3B Q4 (2.0GB) - Good balance"
echo "4) Skip download (I already have a model)"
echo ""
read -p "Enter choice [1-4]: " MODEL_CHOICE

case $MODEL_CHOICE in
    1)
        MODEL_FILE="Phi-3-mini-4k-instruct-q4.gguf"
        MODEL_URL="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
        ;;
    2)
        MODEL_FILE="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        ;;
    3)
        MODEL_FILE="Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        MODEL_URL="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        ;;
    4)
        echo "Skipping model download..."
        MODEL_FILE=""
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

if [ -n "$MODEL_FILE" ]; then
    if [ ! -f "$MODEL_FILE" ]; then
        echo "📥 Downloading $MODEL_FILE (this may take 10-30 minutes)..."
        wget -c "$MODEL_URL" -O "$MODEL_FILE"
        echo -e "${GREEN}✅ Model downloaded${NC}"
    else
        echo -e "${YELLOW}ℹ️  Model already exists, skipping download${NC}"
    fi

    # Update rag_server_pi.py with the model path
    if [ -f "data_processing/rag_server_pi.py" ]; then
        sed -i "s|MODEL_PATH = \".*\"|MODEL_PATH = \"$MODEL_FILE\"|" data_processing/rag_server_pi.py
        echo -e "${GREEN}✅ Updated rag_server_pi.py with model path${NC}"
    fi
fi

# Step 5: Verify required files
echo ""
echo "📦 Step 5/6: Verifying required files..."
MISSING_FILES=()

if [ ! -f "orange_faq.index" ]; then
    MISSING_FILES+=("orange_faq.index")
fi

if [ ! -f "metadata.json" ]; then
    MISSING_FILES+=("metadata.json")
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please run the data processing pipeline first:"
    echo "  python data_processing/clean_orange.py"
    echo "  python data_processing/create_embeddings.py"
    exit 1
fi

echo -e "${GREEN}✅ All required files present${NC}"

# Step 6: Test installation
echo ""
echo "📦 Step 6/6: Testing installation..."
python3 -c "
from llama_cpp import Llama
import faiss
import sentence_transformers
print('✅ All Python packages working')
"

# Installation complete
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or use tmux to keep it running:"
echo "  tmux new -s rag"
echo "  source venv/bin/activate"
echo "  uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000"
echo "  # Press Ctrl+B then D to detach"
echo ""
echo "Test the server:"
echo "  curl http://localhost:8000/health"
echo ""
echo "For automatic startup, see RASPBERRY_PI_SETUP.md (systemd service section)"
echo ""
