"""One deadline for a whole evaluation test, held in front of the LLM client.

See _client.py. The number, EVALUATION_DEADLINE_S, comes from Design Document
v1, EPF-MDE/MATHutrice#66.
"""

from mathutrice.llm_deadline._client import (
    EVALUATION_DEADLINE_S,
    DeadlineClient,
    DeadlineExceeded,
)

__all__ = ["EVALUATION_DEADLINE_S", "DeadlineClient", "DeadlineExceeded"]
