# PDF Data Extraction Application

A Python application for extracting structured data from medical PDF documents using AI-powered processing methods.

## Overview

This application provides two different processing methods for extracting data from PDF files:
- **GenAI Processor**: Uses Google's GenAI (Gemini) models for PDF processing
- **Requesty Processor**: Uses Requesty API with multiple AI model options

## Project Structure

```
extract_pdf_data/
├── README.md                          # Main project documentation (this file)
├── requirements.txt                    # Project dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore file
├── install_dependencies.sh              # Installation script
├── main.py                            # Application entry point
│
├── src/                               # Source code directory
│   ├── __init__.py
│   ├── processors/                     # PDF processing modules
│   │   ├── __init__.py
│   │   ├── base_processor.py          # Abstract base processor (future)
│   │   ├── genai_processor.py         # GenAI processor implementation
│   │   └── requesty_processor.py      # Requesty processor implementation
│   │
│   ├── utils/                          # Utility modules
│   │   ├── __init__.py
│   │   └── logger.py                # Logging module
│   │
│   └── config/                         # Configuration modules
│       ├── __init__.py
│       └── settings.py              # Application settings
│
├── tests/                              # Test files
│   ├── __init__.py
│   ├── test_genai.py             # GenAI processor tests
│   └── test_requesty.py          # Requesty processor tests (future)
│
├── docs/                               # Documentation
│   ├── README_GenAI.md           # GenAI processor documentation
│   ├── README_logging.md         # Logging module documentation
│   ├── API_Reference.md           # API documentation (future)
│   └── DEVELOPMENT.md            # Development guide (future)
│
├── prompts/                            # AI prompts
│   ├── genai_system_prompt.md
│   └── requesty_system_prompt.md
│
├── data/                               # Data directories
│   ├── input/                    # Input PDF files
│   │   └── *.pdf               # PDF files to process
│   ├── output/                   # Processed output files
│   │   └── *.json              # Generated JSON files
│   └── logs/                     # Log files
│       └── *.log               # Application logs
│
└── scripts/                            # Utility scripts (future)
    ├── setup_environment.py       # Environment setup script
    └── batch_process.py          # Batch processing script
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd extract_pdf_data
   ```

2. Install dependencies:
   ```bash
   ./install_dependencies.sh
   # or
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Google GenAI API Configuration
GENAI_API_KEY=your_google_genai_api_key_here

# Requesty API Configuration (if using Requesty processor)
REQUESTY_API_KEY=your_requesty_api_key_here
REQUESTY_BASE_URL=https://your-requesty-api-endpoint.com

# Optional: Custom model selections
# MODEL_GENAI=gemini-2.5-flash
# MODEL_REQUESTY=google/gemini-2.5-pro
```

### Directory Structure

- **Input Directory**: `data/input/` - Place your PDF files here
- **Output Directory**: `data/output/` - Processed JSON files will be saved here
- **Logs Directory**: `data/logs/` - Application logs are stored here

## Usage

### Basic Usage

1. Run the main application:
   ```bash
   python3 main.py
   ```

2. Select a processing option:
   - `1` for GenAI processing
   - `2` for Requesty processing

3. Choose your preferred AI model from the available options

4. The application will process all PDF files in the `data/input/` directory

### Command Line Options

```bash
python3 main.py --choice genai    # Use GenAI processor
python3 main.py --choice requesty  # Use Requesty processor
python3 main.py -c 1              # Use GenAI processor (numeric)
python3 main.py -c 2              # Use Requesty processor (numeric)
```

### Available Models

**GenAI Processor:**
- `gemini-3-pro-preview`
- `gemini-flash-latest`

**Requesty Processor:**
- `vertex/gemini-3-pro-preview`
- `azure/gpt-5.1`
- `bedrock/claude-opus-4-5`
- `bedrock/claude-sonnet-4@eu-west-1`
- `coding/gemini-2.5-flash@europe-west1`
- `google/gemini-2.5-pro`
- `google/gemini-3-pro-preview`
- `vertex/gemini-2.5-flash@europe-west1`

## Output

The application generates:

1. **JSON Output Files**: Named as `{filename}-{processor}-{model}-{timestamp}.json`
2. **Console Output**: Includes detailed summary reports with:
   - Processing time
   - Token usage
   - Extraction statistics
   - Key extracted data

### JSON Structure

The extracted data follows this structure:

```json
{
  "Paciente": {
    "value": "Patient Name",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "FechaNacimiento": {
    "value": "dd/mm/yyyy",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "Sexo": {
    "value": "H|M|U",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "tests": [
    {
      "description": "Test Description",
      "sample_type": "Sample Type",
      "loinc_code": "LOINC Code",
      "page": 1
    }
  ]
}
```

## Development

### Running Tests

```bash
# Run GenAI processor tests
python3 tests/test_genai.py

# Run Requesty processor tests (when available)
python3 tests/test_requesty.py
```

### Code Structure

- **Processors**: Located in `src/processors/`, each implements a specific AI API
- **Utils**: Located in `src/utils/`, shared utilities like logging
- **Config**: Located in `src/config/`, application settings and configuration

### Adding New Processors

1. Create a new processor class in `src/processors/`
2. Inherit from a common base (when implemented)
3. Implement the required methods: `validate_file()`, `process()`
4. Add import to `src/processors/__init__.py`
5. Update `main.py` to include the new processor

## Logging

The application includes comprehensive logging with:
- **Colored console output** for different log levels
- **File logging** with automatic rotation (keeps last 5 days)
- **Full context information** including module, function, and line numbers
- **Runtime configuration** to change log levels

Log files are saved to `data/logs/YYYYMMDD.log`

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are correctly set in `.env` file
2. **File Not Found**: Verify PDF files are placed in `data/input/` directory
3. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
4. **Permission Errors**: Check that the application has read access to input files and write access to output directories

### Getting Help

For issues:
1. Check the logs in `data/logs/` for detailed error messages
2. Verify your API keys are valid and active
3. Ensure the PDF files are readable and not corrupted
4. Check network connectivity for API access

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]