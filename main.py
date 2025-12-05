import os
import sys
import argparse
from typing import List, Optional, Callable, Dict, Any
from dotenv import load_dotenv

# Load environment variables before importing other modules
load_dotenv()

from src.config.settings import INPUT_DIRECTORY, GENAI_MODELS, REQUESTY_MODELS
from src.utils.logger import get_logger, info, warning, error
from src.processors.genai_processor import process_with_genai
from src.processors.requesty_processor import process_with_requesty

# Get a logger instance for this module
logger = get_logger(__name__)

# Processing options constants
GENAI_OPTION = "genai"
REQUESTY_OPTION = "requesty"
PROCESSING_OPTIONS = {
    "1": GENAI_OPTION,
    "2": REQUESTY_OPTION,
    GENAI_OPTION: GENAI_OPTION,
    REQUESTY_OPTION: REQUESTY_OPTION,
}


def demonstrate_logging():
    """Demonstrate the logging module functionality."""
    # Basic logging with different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Logging with custom context
    logger.info(
        "Processing user request", context={"user_id": 12345, "action": "login"}
    )

    # Using the convenience functions
    info("Using the convenience function")
    warning("This is a warning from convenience function")

    # Demonstrate runtime log level change
    print("\n--- Changing log level to WARNING ---")
    from src.utils.logger import set_level

    set_level("WARNING")
    logger.debug("This debug message won't appear")
    logger.info("This info message won't appear")
    logger.warning("This warning message will appear")
    logger.error("This error message will appear")

    # Reset log level
    set_level("DEBUG")

    # Demonstrate exception logging
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("An exception occurred during division")


def get_processing_function(choice: str) -> Callable[[str, str, bool], Dict[str, Any]]:
    """Get the appropriate processing function based on the choice.

    Args:
        choice: The processing choice (genai or requesty).

    Returns:
        The processing function to use.

    Raises:
        ValueError: If the choice is not valid.
    """
    processing_functions = {
        GENAI_OPTION: process_with_genai,
        REQUESTY_OPTION: process_with_requesty,
    }

    if choice not in processing_functions:
        raise ValueError(f"Invalid processing choice: {choice}")

    return processing_functions[choice]


def find_pdf_files(directory: str) -> List[str]:
    """Find all PDF files in the specified directory.

    Args:
        directory: Path to the directory to search.

    Returns:
        List of PDF filenames found in the directory.

    Raises:
        OSError: If there's an error accessing the directory.
    """
    try:
        pdf_files = [
            filename
            for filename in os.listdir(directory)
            if filename.lower().endswith(".pdf")
        ]
        return pdf_files
    except OSError as e:
        raise OSError(f"Error accessing input directory '{directory}': {e}")


def validate_and_normalize_choice(choice: Optional[str]) -> str:
    """Validate and normalize the processing choice.

    Args:
        choice: The user's choice (can be None, "1", "2", "genai", or "requesty").

    Returns:
        The normalized choice ("genai" or "requesty").

    Raises:
        ValueError: If the choice is invalid.
    """
    if choice is None:
        raise ValueError("Choice cannot be None")

    normalized_choice = PROCESSING_OPTIONS.get(choice.lower())
    if normalized_choice is None:
        raise ValueError(f"Invalid choice: {choice}. Must be 1, 2, genai, or requesty.")

    return normalized_choice


def get_streaming_choice() -> bool:
    """Prompt the user to select streaming or non-streaming mode.

    Returns:
        True if streaming is selected, False otherwise.
    """
    while True:
        try:
            choice_input = input("\nEnable streaming (y/n)? [y]: ").strip().lower()
            if choice_input in ["", "y", "yes"]:
                return True
            if choice_input in ["n", "no"]:
                return False
            warning("Invalid choice. Please enter 'y' or 'n'.")
        except EOFError:
            error("No input received. Exiting program.")
            sys.exit(1)


def get_user_choice() -> str:
    """Prompt the user to select a processing option.

    Returns:
        The user's choice ("genai" or "requesty").
    """
    while True:
        print("\nSelect processing option:")
        print("1. genai")
        print("2. requesty")
        try:
            choice_input = input("Enter your choice (1 or 2): ").strip()
        except EOFError:
            error("No input received. Exiting program.")
            sys.exit(1)

        try:
            return validate_and_normalize_choice(choice_input)
        except ValueError:
            warning("Invalid choice. Please enter 1 or 2.")


def show_model_selection_menu(models: dict, option_name: str) -> str:
    """Display a menu of available AI models and get user selection.

    Args:
        models: Dictionary of available models.
        option_name: Name of the processing option (genai or requesty).

    Returns:
        The selected model name.

    Raises:
        SystemExit: If user interrupts the input process.
    """
    print(f"\nSelect AI model for {option_name} processing:")
    for key, model in models.items():
        print(f"{key}. {model}")

    while True:
        try:
            choice_input = input("Enter your choice (1-5): ").strip()
            if choice_input.lower() in ["exit", "quit"]:
                logger.info(f"User chose to exit the model selection for {option_name}")
                sys.exit(0)

            if choice_input in models:
                selected_model = models[choice_input]
                logger.info(f"User selected model for {option_name}: {selected_model}")
                print(f"Selected model: {selected_model}")
                return selected_model
            else:
                warning("Invalid choice. Please enter a number between 1 and 5.")
        except EOFError:
            error("No input received. Exiting program.")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info(f"User interrupted the model selection for {option_name}")
            sys.exit(0)


def process_pdf_files(choice: str, model: str, streaming: bool = True) -> None:
    """Process all PDF files in the input directory using the specified method.

    Args:
        choice: The processing method to use ("genai" or "requesty").
        model: The selected AI model to use for processing.
        streaming: Whether to use streaming for API responses.
    """
    try:
        pdf_files = find_pdf_files(INPUT_DIRECTORY)

        if not pdf_files:
            warning(f"No PDF files found in '{INPUT_DIRECTORY}'")
            return

        info(f"Found {len(pdf_files)} PDF file(s) to process")

        # Get the appropriate processing function
        process_function = get_processing_function(choice)

        # Process each PDF file
        for pdf_file in pdf_files:
            pdf_path = os.path.join(INPUT_DIRECTORY, pdf_file)
            info(f"Processing file: {pdf_file}")
            process_function(pdf_path, model, streaming)

    except OSError as e:
        error(str(e))
        return


def validate_input_directory() -> None:
    """Validate that the input directory exists.

    Raises:
        SystemExit: If the input directory doesn't exist.
    """
    if not os.path.exists(INPUT_DIRECTORY):
        error(f"Input directory '{INPUT_DIRECTORY}' does not exist.")
        sys.exit(1)
    info(f"Input directory '{INPUT_DIRECTORY}' found.")


def start_process(choice: Optional[str] = None) -> None:
    """Main processing function that orchestrates the PDF processing workflow.

    Args:
        choice: Optional processing choice. If None, user will be prompted.
    """
    # Validate input directory
    validate_input_directory()

    # Get or validate the processing choice
    if choice is None:
        choice = get_user_choice()
    else:
        try:
            choice = validate_and_normalize_choice(choice)
        except ValueError as e:
            error(str(e))
            sys.exit(1)

    info(f"Selected option: {choice}")

    # Get model selection based on the processing choice
    if choice == GENAI_OPTION:
        selected_model = show_model_selection_menu(GENAI_MODELS, GENAI_OPTION)
    else:  # REQUESTY_OPTION
        selected_model = show_model_selection_menu(REQUESTY_MODELS, REQUESTY_OPTION)

    # Get streaming preference
    # If choice was provided via CLI, we might want to default to True or add a flag
    # For now, we'll ask if not automated (though here we process interactive flow)
    # Since start_process is the interactive entry point mostly, let's ask.
    # Note: If args.choice is present, we still land here.
    # We should add CLI support for streaming too, but for interactive:
    streaming = get_streaming_choice()
    info(f"Streaming enabled: {streaming}")

    # Process all PDF files with the selected method, model, and streaming preference
    process_pdf_files(choice, selected_model, streaming)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Process PDF data with different options."
    )
    parser.add_argument(
        "--choice", "-c", help="Processing choice: 1, 2, genai, or requesty"
    )
    return parser.parse_args()


def main() -> None:
    """Main application entry point."""
    args = parse_arguments()

    info("Application starting...")
    start_process(args.choice)
    info("Application finished")


if __name__ == "__main__":
    main()
