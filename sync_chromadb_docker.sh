#!/bin/bash
# Script to sync local ChromaDB to remote Docker container
# Usage: ./sync_chromadb_docker.sh [remote_user@remote_host] [container_name]

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
CONTAINER_NAME="${3:-sqlwriter}"
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

echo -e "${GREEN}Syncing ChromaDB to remote Docker container...${NC}"
echo "Local: $LOCAL_CHROMA_DIR"
echo "Remote: $REMOTE_USER@$REMOTE_HOST"
echo "Container: $CONTAINER_NAME"
echo "Remote path: $REMOTE_CHROMA_DIR"
echo ""

# Create temporary archive
TEMP_ARCHIVE="/tmp/chroma_db_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
echo -e "${YELLOW}Creating archive...${NC}"
tar -czf "$TEMP_ARCHIVE" -C "$LOCAL_CHROMA_DIR" .

ARCHIVE_SIZE=$(du -h "$TEMP_ARCHIVE" | cut -f1)
echo -e "${GREEN}Archive created: $TEMP_ARCHIVE (${ARCHIVE_SIZE})${NC}"

# Copy to remote
echo -e "${YELLOW}Copying to remote server...${NC}"
scp "$TEMP_ARCHIVE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Extract into Docker container
echo -e "${YELLOW}Extracting into Docker container...${NC}"
ARCHIVE_NAME=$(basename "$TEMP_ARCHIVE")
ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
    # Check if container exists
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
        echo "Error: Container ${CONTAINER_NAME} not found"
        exit 1
    fi
    
    # Backup existing ChromaDB in container if it exists
    if docker exec ${CONTAINER_NAME} test -d "$REMOTE_CHROMA_DIR"; then
        echo "Backing up existing ChromaDB in container..."
        BACKUP_DIR="${REMOTE_CHROMA_DIR}_backup_\$(date +%Y%m%d_%H%M%S)"
        docker exec ${CONTAINER_NAME} mv "$REMOTE_CHROMA_DIR" "\$BACKUP_DIR" || true
        echo "Backup saved to: \$BACKUP_DIR"
    fi
    
    # Create directory in container
    docker exec ${CONTAINER_NAME} mkdir -p "$REMOTE_CHROMA_DIR"
    
    # Copy archive into container
    docker cp "/tmp/$ARCHIVE_NAME" "${CONTAINER_NAME}:/tmp/"
    
    # Extract archive inside container
    docker exec ${CONTAINER_NAME} tar -xzf "/tmp/$ARCHIVE_NAME" -C "$REMOTE_CHROMA_DIR"
    
    # Set proper permissions
    docker exec ${CONTAINER_NAME} chown -R root:root "$REMOTE_CHROMA_DIR" || true
    docker exec ${CONTAINER_NAME} chmod -R 755 "$REMOTE_CHROMA_DIR" || true
    
    # Clean up archive in container
    docker exec ${CONTAINER_NAME} rm "/tmp/$ARCHIVE_NAME"
    
    # Clean up archive on host
    rm "/tmp/$ARCHIVE_NAME"
    
    echo "ChromaDB synced successfully!"
    echo "Container: ${CONTAINER_NAME}"
    echo "Path: $REMOTE_CHROMA_DIR"
EOF

# Clean up local archive
rm "$TEMP_ARCHIVE"

echo -e "${GREEN}✅ ChromaDB sync completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart the container: ssh $REMOTE_USER@$REMOTE_HOST 'docker restart $CONTAINER_NAME'"
echo "2. Or restart via docker-compose: ssh $REMOTE_USER@$REMOTE_HOST 'cd /path/to/app && docker-compose restart'"

