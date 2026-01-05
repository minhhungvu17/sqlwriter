"""
Database storage for chat threads and saved favorites using ChromaDB.
"""
import logging
from datetime import datetime
from typing import List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ChatStorage:
    """Handles database operations for chat threads and favorites using ChromaDB."""

    def __init__(self, persist_directory: str = "./chroma_db", collection_prefix: str = "chat_"):
        """Initialize with ChromaDB persist directory.
        
        Args:
            persist_directory: Directory where ChromaDB stores data
            collection_prefix: Prefix for collection names (default: "chat_")
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is required for ChatStorage. Install with: pip install chromadb"
            )
        
        self.persist_directory = persist_directory
        self.collection_prefix = collection_prefix
        self._client = None
        self._threads_collection = None
        self._messages_collection = None
        self._favorites_collection = None
        self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self._get_threads_collection()
        self._get_messages_collection()
        self._get_favorites_collection()

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            # Try standard initialization first (works for ChromaDB < 0.5.0)
            try:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False, allow_reset=True),
                )
                # Test if it works by trying to list collections
                try:
                    self._client.list_collections()
                except Exception:
                    # If list_collections fails, might need tenant/database
                    raise ValueError("tenant_required")
            except (ValueError, AttributeError) as e:
                error_str = str(e).lower()
                # If tenant error, try to create tenant first or use admin client
                if "tenant" in error_str or "default_tenant" in error_str or "tenant_required" in error_str:
                    logger.info("ChromaDB requires tenant/database. Attempting to create or use admin client...")
                    try:
                        # Try using AdminClient to create tenant first
                        admin_client = chromadb.AdminClient(settings=Settings(anonymized_telemetry=False))
                        try:
                            admin_client.create_tenant("default_tenant")
                            logger.info("Created default_tenant")
                        except Exception:
                            # Tenant might already exist, that's okay
                            pass
                        try:
                            admin_client.create_database("default_database", tenant="default_tenant")
                            logger.info("Created default_database")
                        except Exception:
                            # Database might already exist, that's okay
                            pass
                        
                        # Now create the persistent client with tenant/database
                        self._client = chromadb.PersistentClient(
                            path=self.persist_directory,
                            tenant="default_tenant",
                            database="default_database",
                            settings=Settings(anonymized_telemetry=False, allow_reset=True),
                        )
                    except Exception as e2:
                        logger.warning(f"Failed to use tenant/database approach: {e2}")
                        logger.warning("Falling back to minimal initialization without tenant/database")
                        # Last resort: try without tenant/database (might work if version supports it)
                        try:
                            self._client = chromadb.PersistentClient(path=self.persist_directory)
                        except Exception as e3:
                            logger.error(f"All ChromaDB initialization methods failed. Last error: {e3}")
                            raise RuntimeError(f"Failed to initialize ChromaDB. Try deleting {self.persist_directory} and restarting, or downgrade chromadb: pip install 'chromadb<0.5.0'") from e3
                else:
                    # Other error, try minimal initialization
                    logger.warning(f"ChromaDB initialization failed, trying minimal setup: {e}")
                    try:
                        self._client = chromadb.PersistentClient(path=self.persist_directory)
                    except Exception as e2:
                        logger.error(f"Failed to initialize ChromaDB client: {e2}")
                        raise
        return self._client

    def _get_threads_collection(self):
        """Get or create threads collection."""
        if self._threads_collection is None:
            client = self._get_client()
            try:
                self._threads_collection = client.get_collection(
                    name=f"{self.collection_prefix}threads",
                    embedding_function=self._embedding_function
                )
            except Exception:
                self._threads_collection = client.create_collection(
                    name=f"{self.collection_prefix}threads",
                    embedding_function=self._embedding_function,
                    metadata={"description": "Chat threads/conversations"}
                )
        return self._threads_collection

    def _get_messages_collection(self):
        """Get or create messages collection."""
        if self._messages_collection is None:
            client = self._get_client()
            try:
                self._messages_collection = client.get_collection(
                    name=f"{self.collection_prefix}messages",
                    embedding_function=self._embedding_function
                )
            except Exception:
                self._messages_collection = client.create_collection(
                    name=f"{self.collection_prefix}messages",
                    embedding_function=self._embedding_function,
                    metadata={"description": "Chat messages"}
                )
        return self._messages_collection

    def _get_favorites_collection(self):
        """Get or create favorites collection."""
        if self._favorites_collection is None:
            client = self._get_client()
            try:
                self._favorites_collection = client.get_collection(
                    name=f"{self.collection_prefix}favorites",
                    embedding_function=self._embedding_function
                )
            except Exception:
                self._favorites_collection = client.create_collection(
                    name=f"{self.collection_prefix}favorites",
                    embedding_function=self._embedding_function,
                    metadata={"description": "Saved favorites"}
                )
        return self._favorites_collection

    # Thread operations
    def create_thread(
        self, thread_id: str, user_id: str, title: str
    ) -> dict:
        """Create a new chat thread."""
        collection = self._get_threads_collection()
        now = datetime.now().isoformat()
        
        metadata = {
            "thread_id": thread_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }
        
        collection.upsert(
            ids=[thread_id],
            documents=[title],  # Store title for potential search
            metadatas=[metadata]
        )
        
        return {
            "id": thread_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
        }

    def get_thread(self, thread_id: str, user_id: str) -> Optional[dict]:
        """Get a thread by ID."""
        collection = self._get_threads_collection()
        try:
            results = collection.get(ids=[thread_id])
            if results["ids"] and len(results["ids"]) > 0:
                metadata = results["metadatas"][0]
                if metadata.get("user_id") == user_id:
                    return {
                        "id": metadata.get("thread_id"),
                        "user_id": metadata.get("user_id"),
                        "title": metadata.get("title"),
                        "created_at": metadata.get("created_at"),
                        "updated_at": metadata.get("updated_at"),
                    }
        except Exception as e:
            logger.debug(f"Error getting thread: {e}")
        return None

    def list_threads(self, user_id: str, limit: int = 20) -> List[dict]:
        """List all threads for a user, ordered by updated_at DESC."""
        collection = self._get_threads_collection()
        try:
            results = collection.get(
                where={"user_id": user_id}
            )
            
            threads = []
            for i, thread_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                threads.append({
                    "id": metadata.get("thread_id"),
                    "user_id": metadata.get("user_id"),
                    "title": metadata.get("title"),
                    "created_at": metadata.get("created_at"),
                    "updated_at": metadata.get("updated_at"),
                })
            
            threads.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return threads[:limit]
        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            return []

    def update_thread_title(self, thread_id: str, user_id: str, title: str) -> bool:
        """Update thread title."""
        collection = self._get_threads_collection()
        try:
            results = collection.get(ids=[thread_id])
            if not results["ids"] or len(results["ids"]) == 0:
                return False
            
            metadata = results["metadatas"][0]
            if metadata.get("user_id") != user_id:
                return False
            
            now = datetime.now().isoformat()
            metadata["title"] = title
            metadata["updated_at"] = now
            
            collection.update(
                ids=[thread_id],
                documents=[title],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating thread: {e}")
            return False

    def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Delete a thread (also deletes associated messages)."""
        collection = self._get_threads_collection()
        messages_collection = self._get_messages_collection()
        try:
            results = collection.get(ids=[thread_id])
            if not results["ids"] or len(results["ids"]) == 0:
                return False
            
            metadata = results["metadatas"][0]
            if metadata.get("user_id") != user_id:
                return False
            
            collection.delete(ids=[thread_id])
            
            try:
                message_results = messages_collection.get(
                    where={"thread_id": thread_id}
                )
                if message_results["ids"]:
                    messages_collection.delete(ids=message_results["ids"])
            except Exception:
                pass
            
            return True
        except Exception as e:
            logger.error(f"Error deleting thread: {e}")
            return False

    # Message operations
    def add_message(
        self, message_id: str, thread_id: str, role: str, content: str
    ) -> dict:
        """Add a message to a thread."""
        collection = self._get_messages_collection()
        now = datetime.now().isoformat()
        
        metadata = {
            "message_id": message_id,
            "thread_id": thread_id,
            "role": role,
            "created_at": now,
        }
        
        collection.upsert(
            ids=[message_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        threads_collection = self._get_threads_collection()
        try:
            thread_results = threads_collection.get(ids=[thread_id])
            if thread_results["ids"]:
                thread_metadata = thread_results["metadatas"][0]
                thread_metadata["updated_at"] = now
                threads_collection.update(
                    ids=[thread_id],
                    documents=[thread_results["documents"][0]],
                    metadatas=[thread_metadata]
                )
        except Exception:
            pass  # Ignore errors updating thread timestamp
        
        return {
            "id": message_id,
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "created_at": now,
        }

    def get_thread_messages(self, thread_id: str, limit: int = 100) -> List[dict]:
        """Get all messages for a thread."""
        collection = self._get_messages_collection()
        try:
            results = collection.get(
                where={"thread_id": thread_id}
            )
            
            messages = []
            for i, message_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                messages.append({
                    "id": metadata.get("message_id"),
                    "thread_id": metadata.get("thread_id"),
                    "role": metadata.get("role"),
                    "content": results["documents"][i],
                    "created_at": metadata.get("created_at"),
                })
            
            messages.sort(key=lambda x: x.get("created_at", ""))
            return messages[:limit]
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    # Favorite operations
    def create_favorite(
        self, favorite_id: str, user_id: str, title: str, type: str, payload: str
    ) -> dict:
        """Create a saved favorite."""
        collection = self._get_favorites_collection()
        now = datetime.now().isoformat()
        
        metadata = {
            "favorite_id": favorite_id,
            "user_id": user_id,
            "title": title,
            "type": type,
            "created_at": now,
        }
        
        collection.upsert(
            ids=[favorite_id],
            documents=[payload],
            metadatas=[metadata]
        )
        
        return {
            "id": favorite_id,
            "user_id": user_id,
            "title": title,
            "type": type,
            "payload": payload,
            "created_at": now,
        }

    def list_favorites(self, user_id: str, limit: int = 20) -> List[dict]:
        """List all favorites for a user."""
        collection = self._get_favorites_collection()
        try:
            results = collection.get(
                where={"user_id": user_id}
            )
            
            favorites = []
            for i, favorite_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                favorites.append({
                    "id": metadata.get("favorite_id"),
                    "user_id": metadata.get("user_id"),
                    "title": metadata.get("title"),
                    "type": metadata.get("type"),
                    "payload": results["documents"][i],
                    "created_at": metadata.get("created_at"),
                })
            
            favorites.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return favorites[:limit]
        except Exception as e:
            logger.error(f"Error listing favorites: {e}")
            return []

    def delete_favorite(self, favorite_id: str, user_id: str) -> bool:
        """Delete a favorite."""
        collection = self._get_favorites_collection()
        try:
            results = collection.get(ids=[favorite_id])
            if not results["ids"] or len(results["ids"]) == 0:
                return False
            
            metadata = results["metadatas"][0]
            if metadata.get("user_id") != user_id:
                return False
            
            collection.delete(ids=[favorite_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting favorite: {e}")
            return False
