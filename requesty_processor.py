"""
Requesty PDF processing module.

This module contains the implementation of the Requesty processing method
for extracting data from PDF files.
"""

import base64
import json
import os
import sys
import re
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, cast

from dotenv import load_dotenv

# Load environment variables before importing other modules
load_dotenv()

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from logger import debug, error, get_logger, info, warning
from settings import REQUESTY_BASE_URL

# Get a logger instance for this module
logger = get_logger(__name__)


class RequestyProcessor:
    """PDF processor using Requesty method."""

    def __init__(self):
        """Initialize the Requesty processor."""
        self.logger = get_logger(f"{__name__}.RequestyProcessor")

        self.api_key = os.environ.get("REQUESTY_API_KEY")
        self.api_endpoint = REQUESTY_BASE_URL

    def validate_file(self, pdf_path: str) -> None:
        """Validate that the PDF file exists and is readable.

        Args:
            pdf_path: Path to the PDF file to validate.

        Raises:
            FileNotFoundError: If the PDF file doesn't exist.
            ValueError: If the file is not a PDF.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.lower().endswith(".pdf"):
            raise ValueError(f"File is not a PDF: {pdf_path}")

        if not os.access(pdf_path, os.R_OK):
            raise PermissionError(f"Cannot read PDF file: {pdf_path}")

        self.logger.debug(f"File validation successful: {pdf_path}")

    def send_to_requesty_api(self, file_path: str, model: str) -> Dict[str, Any]:
        """Send the PDF to Requesty API using the specified model.

        Args:
            file_path: The full path to the PDF file.
            model: The selected AI model to use for processing.

        Returns:
            Dictionary containing the API response.
        """
        self.logger.debug(f"Sending {file_path} to Requesty API using model: {model}")

        # Validate required configuration
        if not self.api_endpoint:
            raise ValueError(
                "REQUESTY_BASE_URL is not configured. Please set the environment variable."
            )

        if not self.api_key:
            raise ValueError(
                "REQUESTY_API_KEY is not configured. Please set the environment variable."
            )

        client = OpenAI(
            base_url=self.api_endpoint,
            api_key=self.api_key,
        )

        try:
            # Read and encode the PDF file as base64
            with open(file_path, "rb") as file:
                file_data = base64.b64encode(file.read()).decode('utf-8')
                self.logger.debug(f"File encoded successfully, size: {len(file_data)} characters")

            # Load system prompt from file
            with open(
                "prompts/requesty_system_prompt.md", "r", encoding="utf-8"
            ) as prompt_file:
                system_prompt = prompt_file.read()

            # Create system message
            system_message: ChatCompletionSystemMessageParam = {
                "role": "system",
                "content": system_prompt,
            }

            # Create user message with model-specific content type
            # Different models expect different formats for file input
            
            # Check if this is a Google Gemini model
            if "google/gemini" in model.lower():
                # Google Gemini models use image_url format with data URI
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the requested fields with bounding boxes from this document.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{file_data}"
                            }
                        }
                    ],
                }
            else:
                # Try file_input format for other models (like Anthropic)
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the requested fields with bounding boxes from this document.",
                        },
                        {
                            "type": "file_input",
                            "filename": os.path.basename(file_path),
                            "file_data": file_data,
                        }
                    ],
                }

            self.logger.debug(f"Sending request to model: {model}")
            
            # Use raw request to bypass OpenAI type checking since Requesty has different format
            messages = [
                system_message,
                user_message  # type: ignore - Requesty API supports file_input type
            ]
            
            # Debug: Log the complete request structure
            self.logger.debug(f"Complete request structure: {json.dumps(messages, indent=2)}")
            
            # Start timing and spinner
            start_time = time.time()
            spinner_active = True
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            
            def show_spinner():
                i = 0
                while spinner_active:
                    print(f"\r\033[36mProcessing PDF with {model}... {spinner_chars[i % len(spinner_chars)]}\033[0m", end="", flush=True)
                    time.sleep(0.1)
                    i += 1
            
            # Start spinner in separate thread
            spinner_thread = threading.Thread(target=show_spinner)
            spinner_thread.daemon = True
            spinner_thread.start()
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore
                    temperature=0.0,
                    timeout=600,  # 10 minutes timeout for the API call to handle long processing
                )
            finally:
                # Stop spinner
                spinner_active = False
                time.sleep(0.2)  # Let spinner finish
                print("\r" + " " * 80 + "\r", end="")  # Clear spinner line
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time

            # Extract the actual response data
            response_content = (
                response.choices[0].message.content
                if response.choices and response.choices[0].message.content
                else ""
            )

            self.logger.debug(f"Received response: {response_content[:200]}...")

            # Only try to parse JSON if we have content
            if response_content:
                try:
                    # Handle markdown code blocks in response
                    # Remove ```json and ``` markers if present
                    cleaned_content = re.sub(r'```json\s*', '', response_content)
                    cleaned_content = re.sub(r'```\s*$', '', cleaned_content)
                    cleaned_content = cleaned_content.strip()
                    
                    data = json.loads(cleaned_content)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON response: {e}")
                    data = {"raw_response": response_content}
            else:
                data = {}

            return {
                "filename": os.path.basename(file_path),
                "model": model,
                "status": "processed",
                "processing_time": processing_time,
                "data": {
                    "response": response_content,
                    "parsed_data": data,
                    "usage": response.usage.model_dump() if response.usage else {},
                },
            }
        except Exception as e:
            self.logger.error(f"Failed to process file with Requesty API: {str(e)}")
            raise

    def process(self, pdf_path: str, model: str) -> Dict[str, Any]:
        """Process a PDF file using Requesty method.

        Args:
            pdf_path: Path to the PDF file to process.
            model: The AI model to use for processing.

        Returns:
            Dictionary containing extracted data and metadata.

        """
        try:
            # Validate the input file
            self.validate_file(pdf_path)
            filename = os.path.basename(pdf_path)

            self.logger.info(
                f"Processing {filename} with Requesty method using model: {model}"
            )

            # Send to Requesty API for analysis with selected model
            api_response = self.send_to_requesty_api(pdf_path, model)

            # Log the API response to terminal with pretty formatting
            self.logger.info("API Response received successfully")
            
            # Pretty print the parsed data if available
            parsed_data = api_response.get("data", {}).get("parsed_data", {})
            if parsed_data and "raw_response" not in parsed_data:
                print("\n" + "="*80)
                print("📄 EXTRACTED DATA FROM PDF")
                print("="*80)
                print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
                print("="*80)
            else:
                print("\n" + "="*80)
                print("⚠️  RAW RESPONSE (JSON parsing failed)")
                print("="*80)
                print(parsed_data.get("raw_response", "No response data"))
                print("="*80)

            # Save the parsed data to JSON file with format: pdffilename-processor-modeselected-datetime.json
            pdf_basename = os.path.splitext(filename)[0]  # Remove .pdf extension
            # Replace forward slashes in model name with dashes to create valid filename
            safe_model_name = model.replace("/", "-")
            
            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{pdf_basename}-requesty-{safe_model_name}-{timestamp}.json"

            # Get the parsed data from the API response
            parsed_data = api_response.get("data", {}).get("parsed_data", {})

            # Save to JSON file in the same directory as the input PDF
            input_dir = os.path.dirname(pdf_path)
            if not input_dir:
                input_dir = "."  # Current directory if no path specified
                
            output_path = os.path.join(input_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as output_file:
                json.dump(parsed_data, output_file, indent=2, ensure_ascii=False)

            self.logger.info(f"Requesty processing completed for {filename}")
            self.logger.info(f"Results saved to {output_path}")

            return {
                "filename": filename,
                "processor": "Requesty",
                "model": model,
                "status": "success",
                "data": api_response,
                "output_file": output_filename,
            }

        except Exception as e:
            self.logger.error(f"Error processing {pdf_path} with Requesty: {str(e)}")
            raise

    def _generate_summary_report(self, filename: str, model: str, api_response: Dict[str, Any], output_path: str, processing_time: float) -> None:
        """Generate a beautiful summary report with colors and timing information."""
        
        # Extract usage data
        usage_data = api_response.get("data", {}).get("usage", {})
        parsed_data = api_response.get("data", {}).get("parsed_data", {})
        
        # Colors for terminal output
        GREEN = '\033[92m'
        BLUE = '\033[94m'
        YELLOW = '\033[93m'
        CYAN = '\033[96m'
        MAGENTA = '\033[95m'
        WHITE = '\033[97m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        # Format time
        if processing_time < 60:
            time_str = f"{processing_time:.2f} seconds"
        else:
            minutes = int(processing_time // 60)
            seconds = processing_time % 60
            time_str = f"{minutes}m {seconds:.2f}s"
        
        # Count extracted fields
        total_fields = len(parsed_data) if isinstance(parsed_data, dict) else 0
        non_null_fields = sum(1 for v in parsed_data.values() if v is not None and v != "" and v != []) if isinstance(parsed_data, dict) else 0
        
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}📊 PROCESSING SUMMARY REPORT{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}")
        
        print(f"\n{GREEN}📁 File Information:{RESET}")
        print(f"   {WHITE}• Filename: {YELLOW}{filename}{RESET}")
        print(f"   {WHITE}• Model: {YELLOW}{model}{RESET}")
        print(f"   {WHITE}• Output: {YELLOW}{output_path}{RESET}")
        
        print(f"\n{GREEN}⏱️  Processing Time:{RESET}")
        print(f"   {WHITE}• Total Time: {YELLOW}{BOLD}{time_str}{RESET}")
        
        if usage_data:
            print(f"\n{GREEN}💰 Token Usage:{RESET}")
            print(f"   {WHITE}• Input Tokens: {YELLOW}{usage_data.get('prompt_tokens', 'N/A')}{RESET}")
            print(f"   {WHITE}• Output Tokens: {YELLOW}{usage_data.get('completion_tokens', 'N/A')}{RESET}")
            print(f"   {WHITE}• Total Tokens: {YELLOW}{usage_data.get('total_tokens', 'N/A')}{RESET}")
            print(f"   {WHITE}• Cost: {YELLOW}${usage_data.get('cost', 'N/A')}{RESET}")
        
        print(f"\n{GREEN}📋 Extraction Results:{RESET}")
        print(f"   {WHITE}• Total Fields: {YELLOW}{total_fields}{RESET}")
        print(f"   {WHITE}• Successfully Extracted: {GREEN}{non_null_fields}{RESET}")
        print(f"   {WHITE}• Success Rate: {YELLOW}{(non_null_fields/total_fields*100):.1f}%{RESET}" if total_fields > 0 else f"   {WHITE}• Success Rate: {YELLOW}N/A{RESET}")
        
        # Show key extracted data
        if isinstance(parsed_data, dict) and parsed_data.get("Paciente"):
            print(f"\n{GREEN}👤 Patient Information:{RESET}")
            patient = parsed_data.get("Paciente", {})
            if patient and patient.get("value"):
                print(f"   {WHITE}• Name: {YELLOW}{patient.get('value')}{RESET}")
            
            birth_date = parsed_data.get("FechaNacimiento", {})
            if birth_date and birth_date.get("value"):
                print(f"   {WHITE}• Birth Date: {YELLOW}{birth_date.get('value')}{RESET}")
                
            sexo = parsed_data.get("Sexo", {})
            if sexo and sexo.get("value"):
                print(f"   {WHITE}• Gender: {YELLOW}{sexo.get('value')}{RESET}")
        
        tests = parsed_data.get("tests", [])
        if tests:
            print(f"\n{GREEN}🧪 Medical Tests ({len(tests)} found):{RESET}")
            for i, test in enumerate(tests[:3], 1):  # Show first 3 tests
                description = test.get("description", "Unknown")
                sample_type = test.get("sample_type", "Unknown")
                print(f"   {WHITE}{i}. {CYAN}{description[:60]}{'...' if len(description) > 60 else ''}{RESET}")
                print(f"      {WHITE}Sample Type: {YELLOW}{sample_type}{RESET}")
            if len(tests) > 3:
                print(f"   {WHITE}... and {len(tests) - 3} more tests{RESET}")
        
        print(f"\n{BOLD}{GREEN}✅ Processing completed successfully!{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")


def process_with_requesty(pdf_path: str, model: str) -> Dict[str, Any]:
    """Process a PDF file using the Requesty method.

    This is a convenience function that maintains compatibility with main.py.

    Args:
        pdf_path: Path to the PDF file to process.
        model: The AI model to use for processing.

    Returns:
        Dictionary containing the processing result.
    """
    try:
        processor = RequestyProcessor()
        result = processor.process(pdf_path, model)
        info(f"Successfully processed {os.path.basename(pdf_path)} with Requesty")
        if result.get("output_file"):
            info(f"Results saved to {result['output_file']}")
        debug(f"Processing result: {result}")
        return result
    except Exception as e:
        error(f"Failed to process {pdf_path} with Requesty: {str(e)}")
        raise
