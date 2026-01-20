import csv
import os
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from vanna.core.enhancer import LlmContextEnhancer, DefaultLlmContextEnhancer


@dataclass
class MappingRow:
    user_term: str
    definition: str
    synonyms: List[str]
    related_schema: str
    sql_rule: str
    keywords: List[str]


class MappingTable:
    def __init__(self, csv_path_candidates: Optional[List[Path]] = None) -> None:
        self.rows: List[MappingRow] = []
        self._load(csv_path_candidates)

    def _load(self, csv_path_candidates: Optional[List[Path]]) -> None:
        candidates = csv_path_candidates or [
            Path(__file__).parent / "business" / "mapping_table.csv",
            Path("business/mapping_table.csv"),
        ]
        csv_path: Optional[Path] = None
        for p in candidates:
            if p.exists():
                csv_path = p
                break
        if not csv_path:
            return

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_term = (row.get("User Term") or "").strip()
                definition = (row.get("User's Definition") or "").strip()
                synonyms_raw = (row.get("Related/Synonyms") or "").strip()
                related_schema = (row.get("Related Schema") or "").strip()
                sql_rule = (row.get("Logic/Filters (The SQL Rule)") or "").strip()
                synonyms = [s.strip() for s in synonyms_raw.split(",") if s.strip()]

                keywords = [user_term.lower()] + [s.lower() for s in synonyms]
                self.rows.append(
                    MappingRow(
                        user_term=user_term,
                        definition=definition,
                        synonyms=synonyms,
                        related_schema=related_schema,
                        sql_rule=sql_rule,
                        keywords=keywords,
                    )
                )

    def find_matches(self, message: str, limit: int = 5) -> List[MappingRow]:
        if not self.rows or not message:
            return []
        text = message.lower()
        matches: List[Tuple[int, MappingRow]] = []
        for r in self.rows:
            score = 0
            for kw in r.keywords:
                if not kw:
                    continue
                # simple case-insensitive substring match; favor longer keywords
                if kw in text:
                    score += max(1, len(kw))
                else:
                    # also try word-boundary match for single-word terms
                    if re.search(rf"\\b{re.escape(kw)}\\b", text):
                        score += max(1, len(kw) - 1)
            if score > 0:
                matches.append((score, r))
        # highest score first, then keep first occurrences
        matches.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in matches[:limit]]


class MappingLlmContextEnhancer(LlmContextEnhancer):
    def __init__(self, mapping_table: MappingTable, agent_memory=None) -> None:
        self.mapping_table = mapping_table
        # compose with default enhancer so we keep memory-based context too
        self.default = DefaultLlmContextEnhancer(agent_memory)
        self._log_enabled = (os.getenv("MAPPING_LOG", "true").lower() in ("1", "true", "yes"))

    async def enhance_system_prompt(self, system_prompt: str, user_message: str, user) -> str:
        # First, let default enhancer add memory context (if any)
        enhanced = await self.default.enhance_system_prompt(system_prompt, user_message, user)

        # Add mapping context
        matches = self.mapping_table.find_matches(user_message, limit=5)
        if not matches:
            return enhanced

        if self._log_enabled:
            try:
                logging.info("Mapping matches for message: %s", user_message)
                for m in matches:
                    # Truncate very long SQL rules for readability
                    rule = m.sql_rule
                    if rule and len(rule) > 400:
                        rule = rule[:400] + "…"
                    logging.info(
                        " - term=%s | schema=%s | rule=%s",
                        m.user_term,
                        m.related_schema,
                        rule or "(none)"
                    )
            except Exception:
                # Never let logging failures affect prompt flow
                pass

        lines: List[str] = []
        lines.append("\n\n## Domain mapping context (use to ground SQL)")
        lines.append("When generating SQL, prefer these schemas and apply these logic filters if relevant to the user's request:")
        for m in matches:
            term = m.user_term or "(unknown term)"
            definition = m.definition or ""
            schema = m.related_schema or ""
            rule = m.sql_rule or ""
            bullet = f"- Term: {term}"
            if definition:
                bullet += f" — {definition}"
            lines.append(bullet)
            if schema:
                lines.append(f"  - related_schema: {schema}")
            if rule:
                lines.append(f"  - sql_rule: {rule}")

        return enhanced + "\n".join(lines)

