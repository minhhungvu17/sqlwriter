#!/bin/bash
# Rebuild frontend script
# Rebuilds the vanna webcomponent after code changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔨 Rebuilding frontend...${NC}"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}❌ Node.js not found. Please install Node.js 22+${NC}"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo -e "${YELLOW}⚠️  Node.js version is too old. Vite requires Node.js 20.19+ or 22.12+${NC}"
    echo "Current version: $(node --version)"
    exit 1
fi

# Navigate to webcomponent directory
cd vanna/frontends/webcomponent

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Build
echo "Building webcomponent..."
npm run build

cd ../../..

echo -e "${GREEN}✅ Frontend rebuilt successfully!${NC}"
echo "You can now run: ./sqlwriter"

