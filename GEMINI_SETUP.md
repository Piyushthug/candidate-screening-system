# Gemini API Setup Guide

This project is now configured to use **Google Gemini API** instead of OpenAI.

## Step 1: Get Your Gemini API Key

1. Visit: https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Select or create a Google Cloud project
4. Copy your API key

## Step 2: Add Key to `.env` File

Open `.env` in the project root and replace:

```env
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE
```

with your actual key:

```env
GOOGLE_API_KEY=AIza...YourActualKeyHere...
```

**⚠️ Important:** Never commit your `.env` file with real keys to Git. It's already in `.gitignore`.

## Step 3: Install Gemini Dependencies

The Gemini packages are being installed. Once complete, verify:

```bash
source .venv/Scripts/activate
pip list | grep -i google
```

You should see:
- `google-generativeai`
- `langchain-google-genai`

## Step 4: Verify Setup

Test the API connection:

```bash
source .venv/Scripts/activate
python -c "import google.generativeai as genai; print('Gemini SDK loaded successfully!')"
```

## Step 5: Start the Server

```bash
source .venv/Scripts/activate
python -m uvicorn backend.main:app --reload
```

Visit: http://127.0.0.1:8000/health

## Configuration

All settings are in `.env`:

```env
# Gemini API Key
GOOGLE_API_KEY=your-key-here

# Model selection
LLM_MODEL=gemini-1.5-flash  # or gemini-1.5-pro for better quality

# Temperature controls randomness
LLM_TEMPERATURE=0.3  # 0 = deterministic, 1 = creative
```

### Available Models

- `gemini-1.5-flash` - Faster, cheaper (default)
- `gemini-1.5-pro` - Better quality, slower
- `gemini-2.0-flash-exp` - Latest experimental

## Troubleshooting

### "API key not valid" error
- Double-check your key is correct
- Ensure no extra spaces before/after key in `.env`
- Verify key is active on https://aistudio.google.com/apikey

### "Could not find a version" during pip install
- Run: `pip install --upgrade langchain-google-genai google-generativeai`
- This installs the latest compatible versions

### Tests failing with API errors
- Unit tests (test_tools.py) don't need API key - they test local logic
- API tests will need valid key if they call Gemini
- For now, focus on unit tests which work without API key

## Testing Without API Key

All core logic tests work without Gemini:

```bash
source .venv/Scripts/activate
pytest tests/test_tools.py -v  # No API needed
pytest tests/test_data_validation.py -v  # No API needed
```

These tests validate the screening logic, fit scoring, and message generation without actually calling Gemini.

## Next Steps

1. ✅ Get Gemini API key from https://aistudio.google.com/apikey
2. ✅ Add key to `.env` file
3. ✅ Run: `pip install -r requirements.txt` (if not already done)
4. ✅ Start server: `python -m uvicorn backend.main:app --reload`
5. ✅ Test: `curl http://127.0.0.1:8000/health`

---

**Status:** Project configured for Gemini API  
**Config File:** `.env`  
**Documentation:** README.md, TEST_STRATEGY.md
