from typing import Type, Optional, List
from pydantic import BaseModel, Field
from vanna.core.tool import Tool, ToolContext, ToolResult


class SeedReferenceArgs(BaseModel):
    question: str = Field(description="User question to match against seeded Q&A")
    k: int = Field(default=3, ge=1, le=10, description="Number of matches to return")
    min_similarity: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Minimum similarity score"
    )


class SeedReferenceTool(Tool[SeedReferenceArgs]):
    @property
    def name(self) -> str:
        return "get_seed_sql_references"

    @property
    def description(self) -> str:
        return (
            "Return up to k SQL examples from seeded Q&A most similar to the question. "
            "Use these as references when forming the final SQL."
        )

    @property
    def access_groups(self) -> list[str]:
        return ["admin", "user"]

    def get_args_schema(self) -> Type[SeedReferenceArgs]:
        return SeedReferenceArgs

    async def execute(self, context: ToolContext, args: SeedReferenceArgs) -> ToolResult:
        # Use tool-usage similarity search so it aligns with Vanna training flow
        search = await context.agent_memory.search_similar_usage(
            question=args.question,
            context=context,
            limit=args.k,
            similarity_threshold=args.min_similarity,
            tool_name_filter="run_sql",
        )

        lines: List[str] = []
        for i, res in enumerate(search, start=1):
            sql = ""
            try:
                sql = (res.memory.args or {}).get("sql", "")
            except Exception:
                sql = ""
            if not sql:
                continue
            lines.append(f"Reference {i} (similarity={res.similarity_score:.2f}):\n{sql}")

        if not lines:
            return ToolResult(
                success=True,
                result_for_llm="No suitable references found.",
            )

        return ToolResult(
            success=True,
            result_for_llm="\n\n".join(lines),
        )


