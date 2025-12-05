#!/usr/bin/env python3
"""
Test script for GenAI processor.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is set
if not os.environ.get("GENAI_API_KEY"):
    print("ERROR: GENAI_API_KEY is not set in environment variables.")
    print("Please set it in your .env file or as an environment variable.")
    sys.exit(1)

try:
    from src.processors.genai_processor import GenAIProcessor
    print("✅ Successfully imported GenAIProcessor")
    
    # Try to initialize the processor
    processor = GenAIProcessor()
    print("✅ Successfully initialized GenAIProcessor")
    
    # Check if we can access the client
    if hasattr(processor, 'client'):
        print("✅ GenAI client is available")
    else:
        print("❌ GenAI client is not available")
        
except ImportError as e:
    print(f"❌ Failed to import GenAIProcessor: {e}")
    print("Please install the required dependencies with: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Failed to initialize GenAIProcessor: {e}")

print("\nTest completed.")