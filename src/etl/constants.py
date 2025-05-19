"""Central knobs."""
from __future__ import annotations

import os

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RETRIES  = 3
TEMPERATURE  = 0.0
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
MAX_CORPUS_CHARS = int(os.getenv("MAX_CORPUS_CHARS", "15000")) 