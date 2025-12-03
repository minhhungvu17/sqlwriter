#!/usr/bin/env python3
"""Utility script to find and delete bad memory entries with SQL syntax errors.

Usage:
    python fix_bad_memories.py --dry-run  # Preview what would be deleted
    python fix_bad_memories.py --delete   # Actually delete bad memories
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from vanna.integrations.chromadb import ChromaAgentMemory
from vanna.core.tool import ToolContext
from vanna.core.user import User

# Load environment variables
load_dotenv()

# Common SQL syntax errors to look for
BAD_PATTERNS = [
    "INNER INNER JOIN",  # Duplicate INNER
    "LEFT LEFT JOIN",    # Duplicate LEFT
    "RIGHT RIGHT JOIN",  # Duplicate RIGHT
    "FULL FULL JOIN",    # Duplicate FULL
    "JOIN JOIN",         # Duplicate JOIN
    "FROM FROM",         # Duplicate FROM
    "WHERE WHERE",       # Duplicate WHERE
    "SELECT SELECT",     # Duplicate SELECT
]


def find_bad_memories(persist_directory: str, collection_name: str):
    """Find memories with SQL syntax errors."""
    memory = ChromaAgentMemory(
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    collection = memory._get_collection()
    
    # Get all memories
    results = collection.get()
    
    if not results["metadatas"] or not results["ids"]:
        print("No memories found.")
        return []
    
    bad_memories = []
    
    for doc_id, metadata in zip(results["ids"], results["metadatas"]):
        # Skip text memories
        if metadata.get("is_text_memory"):
            continue
        
        # Check if this is a tool memory with SQL
        tool_name = metadata.get("tool_name", "")
        if tool_name == "run_sql":
            args_json = metadata.get("args_json", "{}")
            try:
                args = json.loads(args_json)
                sql = args.get("sql", "")
                
                # Check for bad patterns
                for pattern in BAD_PATTERNS:
                    if pattern in sql:
                        bad_memories.append({
                            "id": doc_id,
                            "question": metadata.get("question", ""),
                            "sql_preview": sql[:200] + "..." if len(sql) > 200 else sql,
                            "pattern": pattern,
                            "timestamp": metadata.get("timestamp", ""),
                        })
                        break  # Only report once per memory
            except json.JSONDecodeError:
                pass
    
    return bad_memories


def delete_memory(persist_directory: str, collection_name: str, memory_id: str):
    """Delete a memory by ID."""
    memory = ChromaAgentMemory(
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    
    # Create a dummy context for deletion
    context = ToolContext(
        user=User(id="admin", email="admin@example.com", group_memberships=["admin"]),
        conversation_id="cleanup",
        request_id="cleanup",
        agent_memory=memory,
    )
    
    # Delete the memory
    import asyncio
    deleted = asyncio.run(memory.delete_by_id(context, memory_id))
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Find and delete bad memory entries with SQL syntax errors"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the bad memories",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=None,
        help="ChromaDB persist directory (default: from VANNA_CHROMA_DIR env var)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Collection name (default: from VANNA_CHROMA_COLLECTION env var)",
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.delete:
        parser.print_help()
        print("\nError: Must specify either --dry-run or --delete")
        sys.exit(1)
    
    persist_directory = args.persist_dir or os.getenv("VANNA_CHROMA_DIR", "./chroma_db_data")
    collection_name = args.collection or os.getenv("VANNA_CHROMA_COLLECTION", "vanna_memory")
    
    print(f"Searching for bad memories in: {persist_directory}")
    print(f"Collection: {collection_name}\n")
    
    bad_memories = find_bad_memories(persist_directory, collection_name)
    
    if not bad_memories:
        print("✅ No bad memories found!")
        return
    
    print(f"Found {len(bad_memories)} bad memory(ies):\n")
    
    for i, mem in enumerate(bad_memories, 1):
        print(f"{i}. ID: {mem['id']}")
        print(f"   Question: {mem['question'][:100]}...")
        print(f"   Pattern: {mem['pattern']}")
        print(f"   SQL Preview: {mem['sql_preview']}")
        print(f"   Timestamp: {mem['timestamp']}")
        print()
    
    if args.dry_run:
        print("🔍 DRY RUN: No memories were deleted.")
        print("Run with --delete to actually delete these memories.")
    elif args.delete:
        print("🗑️  Deleting bad memories...")
        deleted_count = 0
        for mem in bad_memories:
            try:
                if delete_memory(persist_directory, collection_name, mem['id']):
                    print(f"✅ Deleted: {mem['id']}")
                    deleted_count += 1
                else:
                    print(f"❌ Failed to delete: {mem['id']}")
            except Exception as e:
                print(f"❌ Error deleting {mem['id']}: {e}")
        
        print(f"\n✅ Deleted {deleted_count}/{len(bad_memories)} bad memories.")


if __name__ == "__main__":
    main()

