# All imports at the top
import os
from pathlib import Path
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool, SaveTextMemoryTool
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.integrations.openai import OpenAILlmService
from vanna.integrations.postgres import PostgresRunner
from vanna.integrations.chromadb import ChromaAgentMemory
from seed_tools import SeedReferenceTool
from seed_rag import seed_on_start

# Load environment variables from .env if present
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

# Configure your LLM
llm = OpenAILlmService(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY")
)

# Configure your database
database_url = os.getenv("DATABASE_URL")
used_fallback_db_url = False
if not database_url:
    used_fallback_db_url = True
    pg_user = os.getenv("POSTGRES_USER", "user")
    pg_password = os.getenv("POSTGRES_PASSWORD", "password")
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_database = os.getenv("POSTGRES_DB", "dbname")
    database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

# If using fallback DB URL, attempt a simple connection to surface errors early
if used_fallback_db_url:
    try:
        import psycopg
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        logging.info("Database connection successful using fallback settings.")
    except Exception as exc:
        parsed = urlparse(database_url)
        db_name = parsed.path.lstrip("/")
        logging.error(
            "Database connection FAILED using fallback settings (host=%s, port=%s, db=%s): %s",
            parsed.hostname,
            parsed.port,
            db_name,
            exc,
        )

db_tool = RunSqlTool(sql_runner=PostgresRunner(connection_string=database_url))

# Configure your agent memory
agent_memory = ChromaAgentMemory(
    collection_name=os.getenv("VANNA_CHROMA_COLLECTION", "vanna_memory"),
    persist_directory=os.getenv("VANNA_CHROMA_DIR", "./chroma_db")
)

# Configure user authentication
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email') or 'minhhung.vu@amili.asia'
        group = 'admin' if user_email == 'minhhung.vu@amili.asia' else 'user'
        return User(id=user_email, email=user_email, group_memberships=[group])

user_resolver = SimpleUserResolver()

# Create your agent
tools = ToolRegistry()
tools.register_local_tool(db_tool, access_groups=['admin', 'user'])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])
tools.register_local_tool(SaveTextMemoryTool(), access_groups=['admin', 'user'])
tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])
tools.register_local_tool(SeedReferenceTool(), access_groups=['admin', 'user'])

agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory
)

# Seed CSV-based references into memory (idempotent via stable IDs)
seed_on_start()

# Run the server
server = VannaFastAPIServer(agent)
port = int(os.getenv("PORT", "8001"))
server.run(host="0.0.0.0", port=port)  # Access at http://localhost:8001