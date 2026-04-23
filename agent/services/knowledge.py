import re
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger('agent')

# Module-level cache so files are read once per process
_cache: dict[str, str] = {}

KNOWLEDGE_FILES = [
    'company_info.md',
    'faq.md',
    'refund_policy.md',
    'shipping_policy.md',
    'account_help.md',
    'escalation_policy.md',
]

# These files are always included regardless of keyword score
ALWAYS_INCLUDE = {'company_info.md'}


class KnowledgeService:
    def __init__(self):
        self.knowledge_dir = Path(settings.KNOWLEDGE_DIR)

    def load_file(self, filename: str) -> str:
        if filename not in _cache:
            path = self.knowledge_dir / filename
            try:
                _cache[filename] = path.read_text(encoding='utf-8')
                logger.debug("Loaded knowledge file | file=%s | chars=%d", filename, len(_cache[filename]))
            except FileNotFoundError:
                logger.warning("Knowledge file not found | file=%s | path=%s", filename, path)
                _cache[filename] = ''
        return _cache[filename]

    def get_relevant_sources(self, query: str, max_sources: int = 3) -> list[dict]:
        """
        Score each knowledge file by keyword overlap with the query.
        Always includes company_info.md as baseline context.
        Returns up to max_sources files, sorted by relevance.
        """
        query_tokens = set(re.findall(r'\b\w+\b', query.lower()))

        scored = []
        for filename in KNOWLEDGE_FILES:
            content = self.load_file(filename)
            if not content:
                continue

            file_tokens = set(re.findall(r'\b\w+\b', content.lower()))
            score = len(query_tokens & file_tokens)

            if filename in ALWAYS_INCLUDE:
                score += 10  # ensure it's always in the top results

            scored.append((score, filename, content))

        scored.sort(key=lambda x: x[0], reverse=True)

        result = []
        seen = set()
        for score, filename, content in scored:
            if len(result) >= max_sources:
                break
            result.append({'filename': filename, 'content': content, 'score': score})
            seen.add(filename)

        logger.debug(
            "Knowledge selection | query=%r | selected=%s",
            query[:60],
            [r['filename'] for r in result],
        )
        return result

    def invalidate_cache(self):
        """Force reload of all files on next access. Useful in tests."""
        _cache.clear()
