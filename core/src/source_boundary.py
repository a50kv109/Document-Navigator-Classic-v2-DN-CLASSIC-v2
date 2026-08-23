"""
DN CLASSIC - SOURCE BOUNDARY
Contract for deterministic source representations.
Defines the minimal interface needed by CORE to anchor and verify text spans.
Does not contain filesystem, zip parsing, LLM or pipeline logic.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    text: str
    
    def verify_span(self, start: int, end: int, expected_text: str) -> bool:
        """
        Validates that the provided span boundaries exactly match the expected text
        within this document.
        """
        if start < 0 or end > len(self.text) or start >= end:
            return False
        return self.text[start:end] == expected_text
