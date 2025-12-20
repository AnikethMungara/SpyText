"""
SpyText - Human-Aligned Document Perception System

A local system for detecting and handling human-invisible text in documents
before content is passed to large language models.
"""

__version__ = "0.1.0"
__author__ = "Aniketh Mungara"
__repository__ = "https://github.com/AnikethMungara/SpyText"

from src.models import TextSpan
from src.ingest import DocumentLoader
from src.extract import PDFExtractor

__all__ = [
    "TextSpan",
    "DocumentLoader",
    "PDFExtractor",
]
