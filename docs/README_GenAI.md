# GenAI PDF Processor

This module provides functionality to extract structured data from medical PDF documents using Google's GenAI (Gemini) models.

## Features

- PDF processing using Google's GenAI models
- Structured data extraction with bounding boxes
- Support for multiple Gemini models
- Detailed logging and progress tracking
- JSON output with extracted medical data
- Summary reports with processing statistics

## Installation

1. Install the required dependencies:

   ```bash
   ./install_dependencies.sh
   ```

2. Set up your environment variables in the `.env` file:

   ```bash
   GENAI_API_KEY=your_google_genai_api_key_here
   ```

## Usage

### Using the main application

1. Run the main application:

   ```bash
   python3 main.py
   ```

2. Select the GenAI processing option (option 1).

3. Choose your preferred Gemini model from the list:
   - gemini-1.5-flash
   - gemini-1.5-pro
   - gemini-2.0-flash-exp
   - gemini-2.5-flash
   - gemini-2.5-pro

4. Place your PDF files in the `input` directory.

5. The application will process all PDF files and save the results as JSON files.

### Using the GenAI processor directly

You can also use the GenAI processor directly in your Python code:

```python
from genai_processor import process_with_genai

# Process a single PDF file
result = process_with_genai("path/to/your/file.pdf", "gemini-2.5-flash")
print(result)
```

## Output

The processor generates:

1. **JSON output file**: Named as `{filename}-genai-{model}-{timestamp}.json`
2. **Console output**: Includes a detailed summary report with:
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
  "DocumentoIdentidad": {
    "value": "ID Number",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "Telefono": {
    "value": "Phone Number",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "NombreMedico": {
    "value": "Doctor Name",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "NumeroColegiado": {
    "value": "Medical ID",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  },
  "NumeroPeticion": [
    {
      "value": "Request Number",
      "page": 1,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "tests": [
    {
      "description": "Test Description",
      "sample_type": "Sample Type",
      "loinc_code": "LOINC Code",
      "page": 1
    }
  ],
  "urine_details": {
    "collection_type": "24h|Spot",
    "volume": "Volume",
    "page": 1,
    "bbox": [x1, y1, x2, y2]
  }
}
```

## Configuration

### Available Models

The GenAI processor supports the following Google models:

1. **gemini-1.5-flash**: Fast and efficient for most tasks
2. **gemini-1.5-pro**: Higher quality for complex documents
3. **gemini-2.0-flash-exp**: Experimental flash model
4. **gemini-2.5-flash**: Latest flash model
5. **gemini-2.5-pro**: Latest pro model with best quality

### System Prompt

The processor uses a specialized system prompt located at `prompts/genai_system_prompt.md` that instructs the model to:

- Extract only information truly present in the document
- Return valid JSON output
- Include bounding boxes for main fields
- Normalize dates and gender values
- Separate all tests into individual entries

## Error Handling

The processor includes comprehensive error handling for:

- File validation and access issues
- API communication problems
- JSON parsing errors
- Model response validation

## Logging

Detailed logs are saved to `logs/app.log` and include:

- Processing steps and timing
- API request/response details
- Error messages and stack traces
- Token usage statistics

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your `GENAI_API_KEY` is correctly set in the `.env` file
2. **File Not Found**: Verify PDF files are placed in the `input` directory
3. **Processing Timeout**: Large files may require more time; consider using flash models for faster processing
4. **JSON Parsing Errors**: Check the raw response in the logs to debug extraction issues

### Getting Help

For issues specific to the GenAI processor:

1. Check the logs in `logs/app.log`
2. Verify your API key is valid and active
3. Ensure the PDF files are readable and not corrupted

For Google GenAI API issues:

- Visit the [Google AI Studio](https://aistudio.google.com/)
- Check the [GenAI documentation](https://ai.google.dev/docs)
