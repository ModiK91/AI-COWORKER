# AI Co-Worker

An AI assistant that understands natural language IT requests and performs real actions (sending emails via Microsoft 365) after human confirmation.

## What it does

- Takes a typed request (e.g. "I forgot my password")
- Uses Claude (Anthropic API) to classify the request into one of: PASSWORD_RESET, CREATE_TICKET, SOFTWARE_ACCESS, or UNKNOWN
- Shows a "Confirm" button before taking any action — the AI suggests, the human approves
- Sends a real email via Microsoft 365 (Authenticated SMTP) confirming the action
- If the request is unrecognized, clearly says so instead of guessing

## Two versions

- **`app.py`** — the main version, a web-based chat interface built with Streamlit
- **`send_email.py`** — an earlier terminal-based version of the same logic, kept for reference

## Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `.\venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with:
    EMAIL_PASSWORD=your_m365_password
    ANTHROPIC_API_KEY=your_anthropic_api_key
5. Run the web app: `streamlit run app.py`
   (or run the terminal version: `python send_email.py`)

## Status

Working prototype: classifies 3 real IT actions with human-confirmed execution, in both a terminal and a web chat interface.

## Next steps

- Add more action types
- Improve conversation memory (multi-turn context for Claude)
- Explore connecting to real enterprise tools (Azure AD, ServiceNow) instead of email