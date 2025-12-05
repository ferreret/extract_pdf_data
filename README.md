# Extract PDF Data

An advanced system for structured data extraction from medical PDF files (analysis requests) using Generative AI models.

This project allows processing individual or batch PDF documents, extracting key information (patient, date, doctor, requested tests, etc.), and exporting it to structured JSON format.

## 🚀 Key Features

*   **Multi-Model Support**: Compatible with a wide range of models through two main processors:
    *   **GenAI Processor**: For Google models (Gemini).
    *   **Requesty Processor**: Compatible with OpenAI-like APIs (GPT-4, Claude, Gemini via Vertex/Google).
*   **Concurrent Execution**: Processes multiple files simultaneously to maximize throughput. (Configurable via `MAX_WORKERS`).
*   **Streaming Mode**: Optional visualization of the response generated token by token (only in sequential mode).
*   **Clean Output**: Console summary reports with color coding, execution times, and token usage.
*   **Data Validation**: Structured and clean extraction of specific medical fields.

## 📋 Prerequisites

*   Python 3.10 or higher.
*   Access to Google GenAI APIs or an OpenAI-compatible provider (like Requesty).

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd extract_pdf_data
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/Mac
    # venv\Scripts\activate   # On Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

Create a `.env` file in the project root based on the following example:

```env
# API Keys
GENAI_API_KEY=your_google_genai_key
REQUESTY_API_KEY=your_requesty_or_other_provider_key

# Base URLs (Optional, for Requesty/OpenAI compatible APIs)
REQUESTY_BASE_URL=https://api.requesty.ai/v1

# Concurrency Configuration
MAX_WORKERS=4  # Maximum number of threads for parallel processing
```

## 💻 Usage

The program features an interactive Command Line Interface (CLI).

1.  **Run the program**:
    ```bash
    python3 main.py
    ```

2.  **Follow the interactive flow**:
    *   **Select Processor**: Choose between `1. genai` or `2. requesty`.
    *   **Select Model**: Choose a specific model from the available list.
    *   **Concurrent Mode**:
        *   `y` (Yes): Processes files in parallel using `MAX_WORKERS`. Streaming mode is automatically disabled to keep the console clean.
        *   `n` (No): Processes files one by one.
    *   **Streaming Mode** (Only if not concurrent):
        *   `y` (Yes): Shows the response generating in real-time.
        *   `n` (No): Waits for the full response.

### Data Output

*   **Console**: Shows progress logs and a final summary report for each file.
*   **JSON Files**: Extracted results are saved in the `data/input/` directory (or where the original PDF is located) with the format:
    `Filename-processor-model-date.json`

## 📂 Project Structure

```
extract_pdf_data/
├── data/
│   ├── input/          # Directory to place PDFs for processing
│   └── logs/           # Log files
├── src/
│   ├── config/         # Configuration and settings
│   ├── processors/     # Processor logic (GenAI, Requesty)
│   ├── utils/          # Utilities (logger, helpers)
│   └── prompts/        # System prompts for models
├── main.py             # Application entry point
├── requirements.txt    # Project dependencies
└── README.md           # Documentation
```
