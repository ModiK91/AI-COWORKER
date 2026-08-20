# AI Co-Worker

An AI assistant that understands natural language requests — both questions and actions — and responds appropriately: answering from company documents, or performing real IT actions after human confirmation.

## What it does

- Classifies each message as one of: PASSWORD_RESET, CREATE_TICKET, SOFTWARE_ACCESS, INCIDENT_REPORT, KNOWLEDGE_QUESTION, or UNKNOWN

- **Actions**: shows a "Confirm" button before sending a real email via Microsoft 365 (Authenticated SMTP) — the AI suggests, the human approves

- **Knowledge questions**: answered using a real local vector database (ChromaDB) —
  1. Documents are chunked and stored permanently in ChromaDB, embedded automatically
  2. The question is embedded and matched against stored chunks via ChromaDB's built-in search
  3. The top matching chunks are sent to Claude, which answers using only that context and cites the source file(s)

- Handles hybrid requests that both ask a question and require an action (e.g. "how do I get VPN access, and can you request it for me?") — answers the question and offers a confirm button for the action, in one response
- In-app document management (sidebar): upload new `.txt`/`.docx`/`.pdf` files directly into the knowledge base (instantly searchable, no restart needed); documents, trash, and the audit log are each shown in collapsible sections (with counts) to keep the sidebar tidy; delete moves a file to a recoverable trash (removed from search, but not permanently erased) with a restore option
- Searches across multiple documents in any mix of `.txt`, `.docx`, and `.pdf` formats, automatically discovered from the `documents/` folder
- Remembers the full conversation, not just the latest message
- Clearly says "I don't know" rather than guessing, for both actions and questions
- Authentication: a simple password gate, real Microsoft Entra ID sign-in (device code flow), or full redirect-based Microsoft Entra ID web login (click to sign in, redirected back automatically) — when signed in with Microsoft, actions use the real signed-in user's email address
- Audit logging: every login and every real action (password reset, ticket, software access, incident report) is recorded with timestamp, user, and details in a local log, viewable in-app via the sidebar
- Loading indicators (spinners) during classification, RAG answering, and document processing, so the app never appears frozen
- Graceful error handling: email failures and document processing failures show a clear, persistent message in the chat (in red) instead of crashing the app, and are never falsely logged as successful actions
- A "New Conversation" button to clear the chat history and any pending action, without logging out
- A welcome message with example prompts shown when starting a new conversation, so new users immediately understand what the assistant can do


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