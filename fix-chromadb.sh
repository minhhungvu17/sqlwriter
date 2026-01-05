#!/bin/bash
# Fix ChromaDB database issues

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 Fixing ChromaDB issues...${NC}"
echo ""

# Find all chroma_db directories
echo "Searching for ChromaDB databases..."
CHROMA_DIRS=$(find . -type d -name "*chroma*" 2>/dev/null | grep -v node_modules | grep -v venv | grep -v __pycache__)

if [ -n "$CHROMA_DIRS" ]; then
    echo -e "${YELLOW}Found ChromaDB directories:${NC}"
    echo "$CHROMA_DIRS"
    echo ""
    
    for dir in $CHROMA_DIRS; do
        echo -e "${YELLOW}Deleting: $dir${NC}"
        rm -rf "$dir"
    done
else
    echo "No chroma_db directories found in current location"
fi

# Also check common locations
COMMON_LOCATIONS=(
    "./chroma_db"
    "/opt/sqlwriter/chroma_db"
    "$HOME/sqlwriter/chroma_db"
    "./chroma_db_data"
)

echo ""
echo "Checking common locations..."
for loc in "${COMMON_LOCATIONS[@]}"; do
    if [ -d "$loc" ]; then
        echo -e "${YELLOW}Found and deleting: $loc${NC}"
        rm -rf "$loc"
    fi
done

echo ""
echo -e "${GREEN}✅ ChromaDB directories deleted${NC}"
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Activating venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ venv not found. Create it first: python3 -m venv venv${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}📦 Reinstalling ChromaDB with compatible version...${NC}"
pip uninstall chromadb -y 2>/dev/null || true
pip install 'chromadb>=0.4.0,<0.5.0'

echo ""
echo -e "${GREEN}✅ Fix complete!${NC}"
echo ""
echo "You can now run: ./run.sh"

