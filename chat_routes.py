"""
API routes for chat history and saved favorites.
"""
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from chat_storage import ChatStorage
from vanna.core.user import UserResolver, RequestContext

logger = logging.getLogger(__name__)


class ThreadCreate(BaseModel):
    id: str
    title: str


class ThreadUpdate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    id: str
    role: str  # 'user' or 'assistant'
    content: str


class FavoriteCreate(BaseModel):
    id: str
    title: str
    type: str  # 'sql' or 'cohort'
    payload: str


def register_chat_storage_routes(
    app, chat_storage: ChatStorage, user_resolver: UserResolver, config: Optional[dict] = None
):
    """Register routes for chat history and favorites."""
    router = APIRouter(prefix="/api/chat", tags=["chat"])
    config = config or {}
    dev_mode = config.get("dev_mode", False)
    cdn_url = config.get("cdn_url", "https://img.vanna.ai/vanna-components.js")
    static_path = config.get("static_path", "/static")

    @app.get("/", response_class=HTMLResponse)
    async def custom_index():
        """Serve the custom chat interface with history and favorites."""
        custom_html_path = Path(__file__).parent / "custom_index.html"
        if custom_html_path.exists():
            with open(custom_html_path, "r") as f:
                html = f.read()
                # Inject the correct script tag
                if dev_mode:
                    script_tag = f'<script type="module" src="{static_path}/vanna-components.js"></script>'
                else:
                    script_tag = f'<script type="module" src="{cdn_url}"></script>'
                # Replace placeholder or add script tag
                if '<script type="module" src="/static/vanna-components.js"></script>' in html:
                    html = html.replace(
                        '<script type="module" src="/static/vanna-components.js"></script>',
                        script_tag
                    )
                elif '<!-- VannaComponentScript -->' in html:
                    html = html.replace('<!-- VannaComponentScript -->', script_tag)
                else:
                    # Insert before closing head tag
                    html = html.replace('</head>', f'    {script_tag}\n</head>')
                return html
        from vanna.servers.base.templates import get_index_html
        return get_index_html(dev_mode=dev_mode, cdn_url=cdn_url)

    async def get_user_id(request: Request) -> str:
        """Extract user ID from request."""
        request_context = RequestContext(
            cookies=dict(request.cookies),
            headers=dict(request.headers),
            remote_addr=request.client.host if request.client else None,
            query_params=dict(request.query_params),
        )
        user = await user_resolver.resolve_user(request_context)
        return user.id

    @router.get("/threads")
    async def list_threads(request: Request):
        """List all threads for the current user."""
        try:
            user_id = await get_user_id(request)
            threads = chat_storage.list_threads(user_id)
            return {"threads": threads}
        except Exception as e:
            logger.error(f"Error listing threads: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/threads")
    async def create_thread(thread_data: ThreadCreate, request: Request):
        """Create a new thread."""
        try:
            user_id = await get_user_id(request)
            thread = chat_storage.create_thread(
                thread_id=thread_data.id,
                user_id=user_id,
                title=thread_data.title,
            )
            return thread
        except Exception as e:
            logger.error(f"Error creating thread: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/threads/{thread_id}")
    async def get_thread(thread_id: str, request: Request):
        """Get a thread by ID."""
        try:
            user_id = await get_user_id(request)
            thread = chat_storage.get_thread(thread_id, user_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            messages = chat_storage.get_thread_messages(thread_id)
            thread["messages"] = messages
            return thread
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting thread: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/threads/{thread_id}")
    async def update_thread(thread_id: str, thread_data: ThreadUpdate, request: Request):
        """Update thread title."""
        try:
            user_id = await get_user_id(request)
            updated = chat_storage.update_thread_title(
                thread_id, user_id, thread_data.title
            )
            if not updated:
                raise HTTPException(status_code=404, detail="Thread not found")
            return {"success": True}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating thread: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/threads/{thread_id}")
    async def delete_thread(thread_id: str, request: Request):
        """Delete a thread."""
        try:
            user_id = await get_user_id(request)
            deleted = chat_storage.delete_thread(thread_id, user_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Thread not found")
            return {"success": True}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting thread: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/threads/{thread_id}/messages")
    async def add_message(thread_id: str, message_data: MessageCreate, request: Request):
        """Add a message to a thread."""
        try:
            user_id = await get_user_id(request)
            thread = chat_storage.get_thread(thread_id, user_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            message = chat_storage.add_message(
                message_id=message_data.id,
                thread_id=thread_id,
                role=message_data.role,
                content=message_data.content,
            )
            return message
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding message: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/favorites")
    async def list_favorites(request: Request):
        """List all favorites for the current user."""
        try:
            user_id = await get_user_id(request)
            favorites = chat_storage.list_favorites(user_id)
            return {"favorites": favorites}
        except Exception as e:
            logger.error(f"Error listing favorites: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/favorites")
    async def create_favorite(favorite_data: FavoriteCreate, request: Request):
        """Create a saved favorite."""
        try:
            user_id = await get_user_id(request)
            favorite = chat_storage.create_favorite(
                favorite_id=favorite_data.id,
                user_id=user_id,
                title=favorite_data.title,
                type=favorite_data.type,
                payload=favorite_data.payload,
            )
            return favorite
        except Exception as e:
            logger.error(f"Error creating favorite: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/favorites/{favorite_id}")
    async def delete_favorite(favorite_id: str, request: Request):
        """Delete a favorite."""
        try:
            user_id = await get_user_id(request)
            deleted = chat_storage.delete_favorite(favorite_id, user_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Favorite not found")
            return {"success": True}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting favorite: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    app.include_router(router)

