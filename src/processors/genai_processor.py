"""
GenAI PDF processing module.

This module contains the implementation of the GenAI processing method
for extracting data from PDF files using Google's GenAI module.
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

from google import genai
from google.genai import types
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.logger import debug, error, get_logger, info, warning
from src.config.settings import GENAI_API_KEY

# Get a logger instance for this module
logger = get_logger(__name__)


class GenAIProcessor:
    """PDF processor using Google's GenAI method."""

    def __init__(self):
        """Initialize the GenAI processor."""
        self.logger = get_logger(f"{__name__}.GenAIProcessor")

        self.api_key = GENAI_API_KEY
        if not self.api_key:
            raise ValueError(
                "GENAI_API_KEY is not configured. Please set the environment variable."
            )

        # Configure the GenAI client with proper timeout
        # Set timeout to 10 minutes for large file processing
        http_options = types.HttpOptions(
            client_args={'timeout': httpx.Timeout(600.0)},  # 10 minutes timeout using httpx.Timeout
            async_client_args={'timeout': httpx.Timeout(600.0)}  # Same timeout for async operations
        )
        self.logger.info(f"Initializing GenAI client with timeout: 600.0 seconds")
        self.client = genai.Client(api_key=self.api_key, http_options=http_options)
        self.logger.info("GenAI client initialized successfully")

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

    def send_to_genai_api(self, file_path: str, model: str) -> Dict[str, Any]:
        """Send the PDF to GenAI API using the specified model.

        Args:
            file_path: The full path to the PDF file.
            model: The selected AI model to use for processing.

        Returns:
            Dictionary containing the API response.
        """
        self.logger.debug(f"Sending {file_path} to GenAI API using model: {model}")

        # Use the selected model directly
        genai_model = model

        try:
            # Load system prompt from file
            with open(
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "genai_system_prompt.md"), "r", encoding="utf-8"
            ) as prompt_file:
                system_prompt = prompt_file.read()

            # Start timing and spinner
            start_time = time.time()
            spinner_active = True
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

            def show_spinner():
                i = 0
                while spinner_active:
                    print(
                        f"\r\033[36mProcessing PDF with {model}... {spinner_chars[i % len(spinner_chars)]}\033[0m",
                        end="",
                        flush=True,
                    )
                    time.sleep(0.1)
                    i += 1

            # Start spinner in separate thread
            spinner_thread = threading.Thread(target=show_spinner)
            spinner_thread.daemon = True
            spinner_thread.start()

            try:
                # Stop the initial spinner and clear the line before starting processing
                spinner_active = False
                time.sleep(0.2)  # Let spinner finish
                print("\r" + " " * 80 + "\r", end="")  # Clear spinner line

                # Upload the file to GenAI
                self.logger.info(f"Uploading file to GenAI...")
                print(f"\033[36mUploading file to GenAI...\033[0m")

                # Re-activate spinner for upload
                spinner_active = True
                spinner_thread = threading.Thread(target=show_spinner)
                spinner_thread.daemon = True
                spinner_thread.start()

                try:
                    # Upload the file
                    file = self.client.files.upload(
                        file=file_path,
                        config=types.UploadFileConfig(
                            display_name=os.path.basename(file_path),
                            mime_type='application/pdf'
                        )
                    )

                    # Wait for processing to complete
                    while file.state == "PROCESSING":
                        time.sleep(2)
                        if file.name:  # Check if name is not None
                            file = self.client.files.get(name=file.name)

                    if file.state == "FAILED":
                        raise ValueError(f"File processing failed: {file.state}")

                    self.logger.debug(f"File uploaded successfully: {file.uri}")

                finally:
                    # Stop upload spinner
                    spinner_active = False
                    time.sleep(0.2)
                    print("\r" + " " * 80 + "\r", end="")  # Clear spinner line

                # Initialize the model
                # The new GenAI client doesn't use GenerativeModel class
                # We'll use the client directly for content generation

                # Start processing spinner
                spinner_active = True
                spinner_thread = threading.Thread(target=show_spinner)
                spinner_thread.daemon = True
                spinner_thread.start()

                try:
                    # Generate content with the file
                    self.logger.info(f"Starting content generation with {model}...")
                    print(f"\033[36mStarting content generation with {model}...\033[0m")

                    # Log the start of API request
                    api_start_time = time.time()
                    self.logger.info(f"Sending API request to generate content with model: {genai_model}")
                    self.logger.debug(f"File URI: {file.uri}")
                    self.logger.debug(f"System prompt length: {len(system_prompt)} characters")

                    # Use streaming with retry and timeout configuration
                    self.logger.info("Starting streaming response...")
                    full_text = ""
                    input_tokens = 0
                    output_tokens = 0
                    
                    # Configure retry policy for transient errors
                    @retry(
                        stop=stop_after_attempt(3),
                        wait=wait_exponential(multiplier=1, min=4, max=10),
                        retry=retry_if_exception_type((httpx.RemoteProtocolError, httpx.ConnectError, ConnectionError))
                    )
                    def make_request():
                        return self.client.models.generate_content(
                            model=genai_model,
                            contents=[
                                file,
                                "Extract the requested fields with bounding boxes from this document.",
                            ],
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.0,
                            ),
                        )
                    
                    try:
                        response = make_request()
                        
                        # Handle response - check if it's a stream or regular response
                        if hasattr(response, 'text'):
                            # Regular response
                            full_text = response.text
                            print(f"\033[36m[RESPONSE] Received response:\033[0m")
                            print(full_text)
                            
                            # Extract usage metadata if available
                            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                                input_tokens = response.usage_metadata.prompt_token_count
                                output_tokens = response.usage_metadata.candidates_token_count
                        else:
                            # Stream response - iterate over response chunks
                            print(f"\033[36m[STREAM] Receiving response:\033[0m")
                            for chunk in response:
                                try:
                                    # Handle different chunk formats
                                    if isinstance(chunk, tuple) and len(chunk) > 1:
                                        # If chunk is a tuple, the second element might contain the content
                                        chunk_content = chunk[1]
                                        if hasattr(chunk_content, 'text') and chunk_content.text:
                                            text = chunk_content.text
                                            print(text, end="", flush=True)
                                            full_text += text
                                    elif hasattr(chunk, 'text') and chunk.text:
                                        # Direct chunk with text
                                        text = chunk.text
                                        print(text, end="", flush=True)
                                        full_text += text
                                except Exception as chunk_error:
                                    self.logger.debug(f"Error processing chunk: {chunk_error}")
                                    pass

                                # Extract usage metadata if available
                                try:
                                    if isinstance(chunk, tuple) and len(chunk) > 1:
                                        chunk_content = chunk[1]
                                        if hasattr(chunk_content, 'usage_metadata') and chunk_content.usage_metadata:
                                            input_tokens = chunk_content.usage_metadata.prompt_token_count or 0
                                            output_tokens = chunk_content.usage_metadata.candidates_token_count or 0
                                    elif hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                                        input_tokens = chunk.usage_metadata.prompt_token_count or 0
                                        output_tokens = chunk.usage_metadata.candidates_token_count or 0
                                except Exception as usage_error:
                                    self.logger.debug(f"Error extracting usage: {usage_error}")

                            print()  # New line after streaming
                        
                        self.logger.info("Response completed successfully")
                        
                    except Exception as stream_error:
                        self.logger.error(f"Request failed: {str(stream_error)}")
                        raise stream_error
                    
                    # Log the completion of API request
                    api_end_time = time.time()
                    api_duration = api_end_time - api_start_time
                    self.logger.info(f"API request completed successfully in {api_duration:.2f} seconds")

                    response_content = full_text if full_text else ""

                finally:
                    # Stop processing spinner
                    spinner_active = False
                    time.sleep(0.2)
                    print("\r" + " " * 80 + "\r", end="")  # Clear spinner line

                # Clean up the uploaded file with proper error handling
                if file.name:  # Check if name is not None
                    try:
                        self.client.files.delete(name=file.name)
                        self.logger.debug(f"Deleted uploaded file: {file.name}")
                    except Exception as delete_error:
                        self.logger.warning(f"Failed to delete uploaded file {file.name}: {str(delete_error)}")

            finally:
                # Ensure spinner is stopped
                spinner_active = False
                time.sleep(0.2)
                print("\r" + " " * 80 + "\r", end="")  # Clear spinner line

            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time

            self.logger.info(f"Content generation completed")
            self.logger.debug(f"Received response: {response_content[:200]}...")

            # Log token usage
            if input_tokens and output_tokens and (input_tokens > 0 or output_tokens > 0):
                self.logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {input_tokens + output_tokens}")

            # Only try to parse JSON if we have content
            if response_content:
                try:
                    # Handle markdown code blocks in response
                    # Remove ```json and ``` markers if present
                    cleaned_content = re.sub(r"```json\s*", "", response_content)
                    cleaned_content = re.sub(r"```\s*$", "", cleaned_content)
                    cleaned_content = cleaned_content.strip()

                    data = json.loads(cleaned_content)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON response: {e}")
                    data = {"raw_response": response_content}
            else:
                data = {}

            # Extract usage data if available
            usage_data = {}
            try:
                if input_tokens and output_tokens and (input_tokens > 0 or output_tokens > 0):
                    usage_data = {
                        "prompt_token_count": input_tokens,
                        "candidates_token_count": output_tokens,
                        "total_token_count": input_tokens + output_tokens,
                    }
                else:
                    self.logger.debug("Usage data not available")
                    usage_data = {"note": "Usage data not available"}
            except Exception as usage_error:
                self.logger.debug(f"Could not extract usage data: {usage_error}")
                usage_data = {"note": "Usage data extraction failed"}

            return {
                "filename": os.path.basename(file_path),
                "model": model,
                "status": "processed",
                "processing_time": processing_time,
                "data": {
                    "response": response_content,
                    "parsed_data": data,
                    "usage": usage_data,
                },
            }
        except Exception as e:
            # Check if it's a timeout-related error
            error_msg = str(e).lower()
            if "timeout" in error_msg or "disconnected" in error_msg:
                self.logger.error(f"Timeout or connection error detected: {str(e)}")
                self.logger.error("This may be due to:")
                self.logger.error("1. Large file size causing processing timeout")
                self.logger.error("2. Network connectivity issues")
                self.logger.error("3. API server-side delays")
                self.logger.error("4. Insufficient timeout configuration")
            else:
                self.logger.error(f"Failed to process file with GenAI API: {str(e)}")
            raise

    def process(self, pdf_path: str, model: str) -> Dict[str, Any]:
        """Process a PDF file using GenAI method.

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
                f"Processing {filename} with GenAI method using model: {model}"
            )

            # Send to GenAI API for analysis with selected model
            api_response = self.send_to_genai_api(pdf_path, model)

            # Log the API response to terminal with pretty formatting
            self.logger.info("API Response received successfully")

            # Pretty print the parsed data if available
            parsed_data = api_response.get("data", {}).get("parsed_data", {})
            if parsed_data and "raw_response" not in parsed_data:
                print("\n" + "=" * 80)
                print("📄 EXTRACTED DATA FROM PDF")
                print("=" * 80)
                print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
                print("=" * 80)
            else:
                print("\n" + "=" * 80)
                print("⚠️  RAW RESPONSE (JSON parsing failed)")
                print("=" * 80)
                print(parsed_data.get("raw_response", "No response data"))
                print("=" * 80)

            # Save the parsed data to JSON file with format: pdffilename-processor-modeselected-datetime.json
            pdf_basename = os.path.splitext(filename)[0]  # Remove .pdf extension
            # Replace forward slashes in model name with dashes to create valid filename
            safe_model_name = model.replace("/", "-")

            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{pdf_basename}-genai-{safe_model_name}-{timestamp}.json"

            # Get the parsed data from the API response
            parsed_data = api_response.get("data", {}).get("parsed_data", {})

            # Save to JSON file in the same directory as the input PDF
            input_dir = os.path.dirname(pdf_path)
            if not input_dir:
                input_dir = "."  # Current directory if no path specified

            output_path = os.path.join(input_dir, output_filename)

            with open(output_path, "w", encoding="utf-8") as output_file:
                json.dump(parsed_data, output_file, indent=2, ensure_ascii=False)

            self.logger.info(f"GenAI processing completed for {filename}")
            self.logger.info(f"Results saved to {output_path}")

            # Generate and display summary report
            self._generate_summary_report(
                filename=filename,
                model=model,
                api_response=api_response,
                output_path=output_path,
                processing_time=api_response.get("processing_time", 0.0),
            )

            return {
                "filename": filename,
                "processor": "GenAI",
                "model": model,
                "status": "success",
                "data": api_response,
                "output_file": output_filename,
            }

        except Exception as e:
            self.logger.error(f"Error processing {pdf_path} with GenAI: {str(e)}")
            raise

    def _generate_summary_report(
        self,
        filename: str,
        model: str,
        api_response: Dict[str, Any],
        output_path: str,
        processing_time: float,
    ) -> None:
        """Generate a beautiful summary report with colors and timing information."""

        # Extract usage data
        usage_data = api_response.get("data", {}).get("usage", {})
        parsed_data = api_response.get("data", {}).get("parsed_data", {})

        # Colors for terminal output
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        MAGENTA = "\033[95m"
        WHITE = "\033[97m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        # Format time
        if processing_time < 60:
            time_str = f"{processing_time:.2f} seconds"
        else:
            minutes = int(processing_time // 60)
            seconds = processing_time % 60
            time_str = f"{minutes}m {seconds:.2f}s"

        # Count extracted fields
        total_fields = len(parsed_data) if isinstance(parsed_data, dict) else 0
        non_null_fields = (
            sum(
                1 for v in parsed_data.values() if v is not None and v != "" and v != []
            )
            if isinstance(parsed_data, dict)
            else 0
        )

        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}📊 PROCESSING SUMMARY REPORT{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}")

        print(f"\n{GREEN}📁 File Information:{RESET}")
        print(f"   {WHITE}• Filename: {YELLOW}{filename}{RESET}")
        print(f"   {WHITE}• Model: {YELLOW}{model}{RESET}")
        print(f"   {WHITE}• Output: {YELLOW}{output_path}{RESET}")

        print(f"\n{GREEN}⏱️  Processing Time:{RESET}")
        print(f"   {WHITE}• Total Time: {YELLOW}{BOLD}{time_str}{RESET}")

        if usage_data and "note" not in usage_data:
            print(f"\n{GREEN}💰 Token Usage:{RESET}")
            print(
                f"   {WHITE}• Input Tokens: {YELLOW}{usage_data.get('prompt_token_count', 'N/A')}{RESET}"
            )
            print(
                f"   {WHITE}• Output Tokens: {YELLOW}{usage_data.get('candidates_token_count', 'N/A')}{RESET}"
            )
            print(
                f"   {WHITE}• Total Tokens: {YELLOW}{usage_data.get('total_token_count', 'N/A')}{RESET}"
            )
        elif usage_data and "note" in usage_data:
            print(f"\n{GREEN}💰 Token Usage:{RESET}")
            print(f"   {WHITE}• {YELLOW}{usage_data.get('note')}{RESET}")

        print(f"\n{GREEN}📋 Extraction Results:{RESET}")
        print(f"   {WHITE}• Total Fields: {YELLOW}{total_fields}{RESET}")
        print(f"   {WHITE}• Successfully Extracted: {GREEN}{non_null_fields}{RESET}")
        print(
            f"   {WHITE}• Success Rate: {YELLOW}{(non_null_fields/total_fields*100):.1f}%{RESET}"
            if total_fields > 0
            else f"   {WHITE}• Success Rate: {YELLOW}N/A{RESET}"
        )

        # Show key extracted data
        if isinstance(parsed_data, dict) and parsed_data.get("Paciente"):
            print(f"\n{GREEN}👤 Patient Information:{RESET}")
            patient = parsed_data.get("Paciente", {})
            if patient and patient.get("value"):
                print(f"   {WHITE}• Name: {YELLOW}{patient.get('value')}{RESET}")

            birth_date = parsed_data.get("FechaNacimiento", {})
            if birth_date and birth_date.get("value"):
                print(
                    f"   {WHITE}• Birth Date: {YELLOW}{birth_date.get('value')}{RESET}"
                )

            sexo = parsed_data.get("Sexo", {})
            if sexo and sexo.get("value"):
                print(f"   {WHITE}• Gender: {YELLOW}{sexo.get('value')}{RESET}")

        tests = parsed_data.get("tests", [])
        if tests:
            print(f"\n{GREEN}🧪 Medical Tests ({len(tests)} found):{RESET}")
            for i, test in enumerate(tests[:3], 1):  # Show first 3 tests
                description = test.get("description", "Unknown")
                sample_type = test.get("sample_type", "Unknown")
                print(
                    f"   {WHITE}{i}. {CYAN}{description[:60]}{'...' if len(description) > 60 else ''}{RESET}"
                )
                print(f"      {WHITE}Sample Type: {YELLOW}{sample_type}{RESET}")
            if len(tests) > 3:
                print(f"   {WHITE}... and {len(tests) - 3} more tests{RESET}")

        print(f"\n{BOLD}{GREEN}✅ Processing completed successfully!{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")

    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """List all uploaded files in the GenAI storage.
        
        Returns:
            List of file information dictionaries.
        """
        try:
            files = []
            for file in self.client.files.list():
                files.append({
                    "name": file.name,
                    "display_name": file.display_name,
                    "size_bytes": file.size_bytes,
                    "state": file.state,
                    "uri": file.uri
                })
            return files
        except Exception as e:
            self.logger.error(f"Failed to list uploaded files: {str(e)}")
            return []

    def cleanup_all_uploaded_files(self) -> Dict[str, Any]:
        """Clean up all uploaded files in the GenAI storage.
        
        Returns:
            Dictionary with cleanup results including success/failure counts.
        """
        try:
            uploaded_files = self.list_uploaded_files()
            total_files = len(uploaded_files)
            deleted_count = 0
            failed_count = 0
            failed_files = []
            
            self.logger.info(f"Found {total_files} uploaded files to clean up")
            
            for file_info in uploaded_files:
                file_name = file_info.get("name")
                if file_name:
                    try:
                        self.client.files.delete(name=file_name)
                        self.logger.debug(f"Deleted uploaded file: {file_name}")
                        deleted_count += 1
                    except Exception as delete_error:
                        self.logger.warning(f"Failed to delete uploaded file {file_name}: {str(delete_error)}")
                        failed_count += 1
                        failed_files.append({"name": file_name, "error": str(delete_error)})
            
            result = {
                "total_files": total_files,
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "failed_files": failed_files
            }
            
            self.logger.info(f"Cleanup completed: {deleted_count}/{total_files} files deleted successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup uploaded files: {str(e)}")
            return {"error": str(e)}


def process_with_genai(pdf_path: str, model: str) -> Dict[str, Any]:
    """Process a PDF file using the GenAI method.

    This is a convenience function that maintains compatibility with main.py.

    Args:
        pdf_path: Path to the PDF file to process.
        model: The AI model to use for processing.

    Returns:
        Dictionary containing the processing result.
    """
    try:
        processor = GenAIProcessor()
        result = processor.process(pdf_path, model)
        info(f"Successfully processed {os.path.basename(pdf_path)} with GenAI")
        if result.get("output_file"):
            info(f"Results saved to {result['output_file']}")
        # debug(f"Processing result: {result}")
        return result
    except Exception as e:
        error(f"Failed to process {pdf_path} with GenAI: {str(e)}")
        raise
