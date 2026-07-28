# AI Co-Worker

A command-line AI assistant that understands natural language requests and performs real IT actions (sending emails via Microsoft 365) after human confirmation.

## What it does

- Takes a typed request (e.g. "I forgot my password")
- Uses Claude (Anthropic API) to classify the request into one of: PASSWORD_RESET, CREATE_TICKET, SOFTWARE_ACCESS, or UNKNOWN
- Asks the user to confirm before taking any action
- Sends a real email via Microsoft 365 (Authenticated SMTP) confirming the action

## Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `.\venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with:
    EMAIL_PASSWORD=your_m365_password
    ANTHROPIC_API_KEY=your_anthropic_api_key
5. Run it: `python send_email.py`

## Status

Work in progress — currently a terminal-based prototype. Next step: building a Streamlit web chat interface.