"""
PDF Processors Module

This package contains different processor implementations for extracting data from PDF files.
"""

from .genai_processor import GenAIProcessor, process_with_genai
from .requesty_processor import RequestyProcessor, process_with_requesty

__all__ = [
    'GenAIProcessor',
    'process_with_genai',
    'RequestyProcessor', 
    'process_with_requesty'
]