# Fact-Checking Web App

A web application that automatically extracts claims from PDF documents and verifies them against live web data using AI and web search APIs.

## Features

- **PDF Upload**: Drag-and-drop interface for uploading PDF documents
- **Claim Extraction**: Automatically identifies verifiable claims (statistics, dates, financial figures, technical specs)
- **Web Verification**: Searches the live web to verify claims against current data
- **Status Classification**: Flags claims as:
  - ✅ **VERIFIED**: Matches current data
  - ⚠️ **INACCURATE**: Outdated or partially incorrect
  - ❌ **FALSE**: No evidence found or contradicts evidence
- **Detailed Reports**: Provides explanations, correct information, and source citations

## Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: OpenAI GPT-4o-mini
- **Web Search**: Tavily API
- **PDF Processing**: pdfplumber

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd new-one
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

**Getting API Keys:**
- **OpenAI**: Sign up at [OpenAI Platform](https://platform.openai.com/) and create an API key
- **Tavily**: Sign up at [Tavily](https://tavily.com/) and get your API key

### 4. Run the Application

```bash
  streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your environment variables (OPENAI_API_KEY and TAVILY_API_KEY) in the app settings
5. Deploy!

### Other Platforms

The app can also be deployed on:
- **Vercel**: Use the Streamlit buildpack
- **Render**: Create a web service with the command `streamlit run app.py`
- **Heroku**: Use the Streamlit buildpack

## How It Works

1. **PDF Upload**: User uploads a PDF document
2. **Text Extraction**: The app extracts all text from the PDF
3. **Claim Extraction**: OpenAI analyzes the text and identifies verifiable claims
4. **Web Search**: For each claim, Tavily searches the web for current information
5. **Verification**: OpenAI compares the claim against search results and determines verification status
6. **Results Display**: Results are shown with status, explanations, and source citations

## Example Usage

1. Upload a PDF containing claims (e.g., a document with statistics, dates, or financial figures)
2. Click "Verify All Claims"
3. Review the verification results showing which claims are verified, inaccurate, or false
4. Check the explanations and source citations for each claim

## Requirements

- Python 3.8+
- OpenAI API key
- Tavily API key

## License

MIT License

