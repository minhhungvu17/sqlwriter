#!/bin/bash
# Reinstall vanna package properly

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 Reinstalling vanna package...${NC}"
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    if [ -d "venv" ]; then
        echo "Activating venv..."
        source venv/bin/activate
    else
        echo -e "${RED}❌ venv not found. Create it first: python3 -m venv venv${NC}"
        exit 1
    fi
fi

echo "1. Uninstalling old vanna package..."
pip uninstall vanna -y 2>/dev/null || true

echo ""
echo "2. Upgrading pip..."
pip install --upgrade pip

echo ""
echo "3. Installing vanna in editable mode with all extras..."
pip install -e ./vanna[fastapi,openai,postgres,chromadb]

echo ""
echo "4. Verifying installation..."
if python3 -c "from vanna.integrations.chromadb import ChromaAgentMemory; print('✅ ChromaDB integration available')" 2>/dev/null; then
    echo -e "${GREEN}✅ Vanna installed successfully!${NC}"
else
    echo -e "${RED}❌ Installation verification failed${NC}"
    echo ""
    echo "Checking what's installed..."
    pip show vanna || echo "Vanna not found in pip"
    echo ""
    echo "Checking if module exists..."
    ls -la vanna/src/vanna/integrations/chromadb/__init__.py || echo "Module file not found"
    echo ""
    echo "Trying to check Python path..."
    python3 -c "import sys; print('Python path:'); [print(p) for p in sys.path]"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Done! You can now run: ./run.sh${NC}"

