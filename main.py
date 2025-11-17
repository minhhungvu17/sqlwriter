# All imports at the top
import os
from pathlib import Path
from dotenv import load_dotenv
from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.core.tool import ToolContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool, SaveTextMemoryTool
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.integrations.azureopenai import AzureOpenAILlmService
from vanna.integrations.postgres import PostgresRunner
from vanna.integrations.chromadb import ChromaAgentMemory
import asyncio
import csv

# Load environment variables from .env if present
load_dotenv()

# Configure your LLM
llm = AzureOpenAILlmService(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Configure your database
database_url = os.getenv("DATABASE_URL")
if not database_url:
    pg_user = os.getenv("POSTGRES_USER", "user")
    pg_password = os.getenv("POSTGRES_PASSWORD", "password")
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_database = os.getenv("POSTGRES_DB", "dbname")
    database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

db_tool = RunSqlTool(sql_runner=PostgresRunner(connection_string=database_url))

# Configure your agent memory (toggle-aware wrapper)
class ToggleableAgentMemory(ChromaAgentMemory):
    def _is_enabled(self, context: ToolContext) -> bool:
        try:
            return bool(context.user.metadata.get("use_business_context", True))
        except Exception:
            return True

    async def search_text_memories(self, query: str, context: ToolContext, *, limit: int = 10, similarity_threshold: float = 0.7):
        if not self._is_enabled(context):
            return []
        return await super().search_text_memories(query, context, limit=limit, similarity_threshold=similarity_threshold)

    async def get_recent_text_memories(self, context: ToolContext, limit: int = 10):
        if not self._is_enabled(context):
            return []
        return await super().get_recent_text_memories(context, limit=limit)

agent_memory = ToggleableAgentMemory(
    collection_name=os.getenv("VANNA_CHROMA_COLLECTION", "vanna_memory"),
    persist_directory=os.getenv("VANNA_CHROMA_DIR", "./chroma_db")
)

# Configure user authentication
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email') or 'minhhung.vu@amili.asia'
        group = 'admin' if user_email == 'minhhung.vu@amili.asia' else 'user'
        # use_business_context_cookie = request_context.get_cookie('use_business_context')
        # use_business_context = True if (use_business_context_cookie is None or use_business_context_cookie == '1') else False
        return User(id=user_email, email=user_email, group_memberships=[group])

user_resolver = SimpleUserResolver()

# Create your agent
tools = ToolRegistry()
tools.register_local_tool(db_tool, access_groups=['admin', 'user'])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])
tools.register_local_tool(SaveTextMemoryTool(), access_groups=['admin', 'user'])
tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])

agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory
)

# Seed business context into agent memory
async def seed_business_context() -> None:
    admin_user = User(id='minhhung.vu@amili.asia', email='minhhung.vu@amili.asia', group_memberships=['admin'])
    ctx = ToolContext(
        user=admin_user,
        conversation_id="setup",
        request_id="seed-business-context",
        agent_memory=agent_memory,
        metadata={}
    )
    schema_path = Path(__file__).parent / "business" / "schema_explanation.txt"
    try:
        content = schema_path.read_text(encoding="utf-8").strip()
    except Exception:
        content = ""
    if content:
        await agent.agent_memory.save_text_memory(content=content, context=ctx)

# Seed a known Question -> SQL pair into tool memory
async def seed_qna_memory() -> None:
    admin_user = User(id='minhhung.vu@amili.asia', email='minhhung.vu@amili.asia', group_memberships=['admin'])
    ctx = ToolContext(
        user=admin_user,
        conversation_id="setup",
        request_id="seed-qna-memory",
        agent_memory=agent_memory,
        metadata={}
    )
    csv_path = Path(__file__).parent / "business" / "seed_qna.csv"
    if not csv_path.exists():
        return
    try:
        with csv_path.open(mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                question = (row.get("question") or "").strip()
                sql = (row.get("sql") or "").strip()
                if not question or not sql:
                    continue
                await agent.agent_memory.save_tool_usage(
                    question=question,
                    tool_name="run_sql",
                    args={"sql": sql},
                    context=ctx,
                    success=True,
                )
    except Exception:
        # Fail quietly if CSV malformed; avoid blocking server start
        pass

# Run the server
# asyncio.run(seed_business_context())
asyncio.run(seed_qna_memory())
server = VannaFastAPIServer(agent)
server.run()  # Access at http://localhost:8000