#!/bin/bash
# Script to sync local ChromaDB to remote server
# Usage: ./sync_chromadb.sh [remote_user@remote_host] [remote_path]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
LOCAL_CHROMA_DIR="./chroma_db"
REMOTE_USER="${1:-root}"
REMOTE_HOST="${2:-your-remote-server.com}"
REMOTE_PATH="${3:-/opt/sqlwriter/chroma_db}"

# Check if local ChromaDB exists
if [ ! -d "$LOCAL_CHROMA_DIR" ]; then
    echo -e "${RED}Error: Local ChromaDB directory not found: $LOCAL_CHROMA_DIR${NC}"
    exit 1
fi

if [ ! -f "$LOCAL_CHROMA_DIR/chroma.sqlite3" ]; then
    echo -e "${RED}Error: chroma.sqlite3 not found in $LOCAL_CHROMA_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Syncing ChromaDB from local to remote...${NC}"
echo "Local: $LOCAL_CHROMA_DIR"
echo "Remote: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"
echo ""

# Create temporary archive
TEMP_ARCHIVE="/tmp/chroma_db_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
echo -e "${YELLOW}Creating archive...${NC}"
tar -czf "$TEMP_ARCHIVE" -C "$LOCAL_CHROMA_DIR" .

# Get archive size
ARCHIVE_SIZE=$(du -h "$TEMP_ARCHIVE" | cut -f1)
echo -e "${GREEN}Archive created: $TEMP_ARCHIVE (${ARCHIVE_SIZE})${NC}"

# Copy to remote
echo -e "${YELLOW}Copying to remote server...${NC}"
scp "$TEMP_ARCHIVE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Extract on remote
echo -e "${YELLOW}Extracting on remote server...${NC}"
ARCHIVE_NAME=$(basename "$TEMP_ARCHIVE")
ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
    # Backup existing ChromaDB if it exists
    if [ -d "$REMOTE_PATH" ]; then
        echo "Backing up existing ChromaDB..."
        BACKUP_DIR="${REMOTE_PATH}_backup_\$(date +%Y%m%d_%H%M%S)"
        mv "$REMOTE_PATH" "\$BACKUP_DIR"
        echo "Backup saved to: \$BACKUP_DIR"
    fi
    
    # Create directory if it doesn't exist
    mkdir -p "$REMOTE_PATH"
    
    # Extract archive
    tar -xzf "/tmp/$ARCHIVE_NAME" -C "$REMOTE_PATH"
    
    # Set proper permissions (adjust as needed)
    chown -R root:root "$REMOTE_PATH" || true
    chmod -R 755 "$REMOTE_PATH" || true
    
    # Clean up archive
    rm "/tmp/$ARCHIVE_NAME"
    
    echo "ChromaDB synced successfully!"
    echo "Remote path: $REMOTE_PATH"
EOF

# Clean up local archive
rm "$TEMP_ARCHIVE"

echo -e "${GREEN}✅ ChromaDB sync completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart the remote Docker container: docker restart sqlwriter"
echo "2. Or restart the remote service"

