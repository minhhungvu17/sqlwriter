#!/bin/bash
# SQLWriter startup script
# Automatically activates venv, rebuilds frontend if needed, and runs the server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting SQLWriter...${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python3 -c "import vanna" 2>/dev/null || ! python3 -c "import dotenv" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Installing...${NC}"
    pip install --upgrade pip
    
    # Install vanna package first
    pip install -e ./vanna[fastapi,openai,postgres,chromadb]
    
    # Install all other dependencies from requirements.txt
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Check if frontend is built
FRONTEND_DIST="vanna/frontends/webcomponent/dist/vanna-components.js"
if [ ! -f "$FRONTEND_DIST" ]; then
    echo -e "${YELLOW}⚠️  Frontend not built. Building...${NC}"
    cd vanna/frontends/webcomponent
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install
    fi
    
    npm run build
    cd ../../..
    echo -e "${GREEN}✅ Frontend built${NC}"
else
    echo -e "${GREEN}✅ Frontend already built${NC}"
fi

# Run the server
echo -e "${GREEN}🎯 Starting server...${NC}"
echo ""
python3 main.py

