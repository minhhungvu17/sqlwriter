#!/bin/bash
# Script to sync local ChromaDB to remote server (REPLACE, not backup)
# Usage: ./sync_chromadb_remote.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LOCAL_CHROMA_DIR="./chroma_db"
SSH_KEY="$HOME/.ssh/amili-stg"
REMOTE_USER="ubuntu"
REMOTE_HOST="10.100.8.252"
CONTAINER_NAME="sqlwriter"
REMOTE_CHROMA_DIR="/opt/sqlwriter/chroma_db"

# Check if local ChromaDB exists
if [ ! -d "$LOCAL_CHROMA_DIR" ]; then
    echo -e "${RED}Error: Local ChromaDB directory not found: $LOCAL_CHROMA_DIR${NC}"
    exit 1
fi

if [ ! -f "$LOCAL_CHROMA_DIR/chroma.sqlite3" ]; then
    echo -e "${RED}Error: chroma.sqlite3 not found in $LOCAL_CHROMA_DIR${NC}"
    exit 1
fi

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found: $SSH_KEY${NC}"
    exit 1
fi

echo -e "${GREEN}Syncing ChromaDB to remote server (REPLACING existing)...${NC}"
echo "Local: $LOCAL_CHROMA_DIR"
echo "Remote: $REMOTE_USER@$REMOTE_HOST"
echo "Container: $CONTAINER_NAME"
echo "Remote path: $REMOTE_CHROMA_DIR"
echo ""

# Create temporary archive
TEMP_ARCHIVE="/tmp/chroma_db_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
echo -e "${YELLOW}Creating archive from local ChromaDB...${NC}"
tar -czf "$TEMP_ARCHIVE" -C "$LOCAL_CHROMA_DIR" .

ARCHIVE_SIZE=$(du -h "$TEMP_ARCHIVE" | cut -f1)
echo -e "${GREEN}Archive created: $TEMP_ARCHIVE (${ARCHIVE_SIZE})${NC}"

# Copy to remote
echo -e "${YELLOW}Copying archive to remote server...${NC}"
scp -i "$SSH_KEY" "$TEMP_ARCHIVE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Extract into Docker container (REPLACE existing)
echo -e "${YELLOW}Replacing ChromaDB in Docker container...${NC}"
ARCHIVE_NAME=$(basename "$TEMP_ARCHIVE")
ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" << EOF
    set -e
    
    # Check if container exists
    if ! sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
        echo "Error: Container ${CONTAINER_NAME} not found"
        exit 1
    fi
    
    echo "Removing existing ChromaDB..."
    # Remove existing ChromaDB directory completely
    sudo docker exec ${CONTAINER_NAME} rm -rf "$REMOTE_CHROMA_DIR" || true
    
    # Create fresh directory
    echo "Creating new ChromaDB directory..."
    sudo docker exec ${CONTAINER_NAME} mkdir -p "$REMOTE_CHROMA_DIR"
    
    # Copy archive into container
    echo "Copying archive into container..."
    sudo docker cp "/tmp/$ARCHIVE_NAME" "${CONTAINER_NAME}:/tmp/"
    
    # Extract archive inside container
    echo "Extracting archive..."
    sudo docker exec ${CONTAINER_NAME} tar -xzf "/tmp/$ARCHIVE_NAME" -C "$REMOTE_CHROMA_DIR"
    
    # Set proper permissions
    echo "Setting permissions..."
    sudo docker exec ${CONTAINER_NAME} chown -R root:root "$REMOTE_CHROMA_DIR" || true
    sudo docker exec ${CONTAINER_NAME} chmod -R 755 "$REMOTE_CHROMA_DIR" || true
    
    # Clean up archive in container
    sudo docker exec ${CONTAINER_NAME} rm "/tmp/$ARCHIVE_NAME"
    
    # Clean up archive on host
    rm "/tmp/$ARCHIVE_NAME"
    
    echo ""
    echo -e "\033[0;32m✅ ChromaDB replaced successfully!\033[0m"
    echo "Container: ${CONTAINER_NAME}"
    echo "Path: $REMOTE_CHROMA_DIR"
    
    # Show what was synced
    echo ""
    echo "Verifying sync..."
    sudo docker exec ${CONTAINER_NAME} ls -lh "$REMOTE_CHROMA_DIR" || true
EOF

# Clean up local archive
rm "$TEMP_ARCHIVE"

echo ""
echo -e "${GREEN}✅ ChromaDB sync completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart the container:"
echo "   ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST 'sudo docker restart $CONTAINER_NAME'"
echo ""
echo "2. Verify it's working:"
echo "   ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST 'sudo docker logs $CONTAINER_NAME --tail 50'"

