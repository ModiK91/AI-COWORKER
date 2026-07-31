# AI Co-Worker

An AI assistant that understands natural language requests — both questions and actions — and responds appropriately: answering from company documents, or performing real IT actions after human confirmation.

## What it does

- Classifies each message as one of: PASSWORD_RESET, CREATE_TICKET, SOFTWARE_ACCESS, KNOWLEDGE_QUESTION, or UNKNOWN
- **Actions**: shows a "Confirm" button before sending a real email via Microsoft 365 (Authenticated SMTP) — the AI suggests, the human approves
- **Knowledge questions**: answered using a two-stage RAG pipeline —
  1. Claude identifies which document chunks are relevant to the question
  2. Claude answers using only those chunks, citing the source file(s)
- Searches across multiple documents (`company_policy.txt`, `it_security_policy.txt`)
- Remembers the full conversation, not just the latest message
- Clearly says "I don't know" rather than guessing, for both actions and questions

## Two versions

- **`app.py`** — the main version, a web-based chat interface built with Streamlit
- **`send_email.py`** — an earlier terminal-based version of the action-only logic, kept for reference
- **`test_rag.py`** — isolated RAG experiments, used to build and test the retrieval logic before merging into `app.py`

## Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `.\venv\Scripts\Activate.ps1` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with:
    EMAIL_PASSWORD=your_m365_password
    ANTHROPIC_API_KEY=your_anthropic_api_key
5. Run the web app: `streamlit run app.py`

## Status

Working prototype with both core capabilities unified: RAG-based question answering (multi-document, relevance-filtered, cited) and human-confirmed action execution.

## Next steps

- Add authentication (Entra ID login)
- Replace email actions with real Azure AD / ServiceNow API calls
- Add more documents and more action types
- Consider proper vector embeddings (Azure AI Search) if document count grows significantly