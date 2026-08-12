import smtplib  # Python's built-in tool for sending emails
import os  # Lets us access those loaded secrets
import streamlit as st  # Imports Streamlit
import glob  # Python's built-in tool for finding files matching a pattern (like "all .txt files in a folder")
import chromadb  # Imports the vector database tool
import msal  # Imports Microsoft's authentication library

from dotenv import load_dotenv  # Lets us read secrets from .env
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude
from docx import Document  # Imports the tool for reading Word (.docx) files
from pypdf import PdfReader  # Imports the tool for reading PDF files

load_dotenv()  # Loads ANTHROPIC_API_KEY from .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates our connection to Claude

@st.cache_resource  # Ensures we set up the MSAL connection only once
def get_msal_app():  # A function that creates and returns our connection to Microsoft's sign-in system
    tenant_id = os.getenv("AZURE_TENANT_ID")  # Your organization's ID
    client_id = os.getenv("AZURE_CLIENT_ID")  # This app's ID
    authority = f"https://login.microsoftonline.com/{tenant_id}"  # Your organization's login address
    return msal.PublicClientApplication(client_id, authority=authority)  # Creates the connection

msal_app = get_msal_app()  # Gets the cached connection

@st.cache_resource  # Ensures we set up this connection only once
def get_msal_web_app():  # A function for the web-redirect version of login
    tenant_id = os.getenv("AZURE_TENANT_ID")  # Your organization's ID
    client_id = os.getenv("AZURE_CLIENT_ID")  # This app's ID
    client_secret = os.getenv("AZURE_CLIENT_SECRET")  # This app's secret, proving its identity to Microsoft
    authority = f"https://login.microsoftonline.com/{tenant_id}"  # Your organization's login address
    return msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)  # Creates a connection that can securely exchange codes for tokens

msal_web_app = get_msal_web_app()  # Gets the cached connection

REDIRECT_URI = "http://localhost:8501"  # Must exactly match what we registered in Entra ID

@st.cache_resource  # Ensures we connect to the database only once, not on every interaction
def get_chroma_collection():  # A function that sets up and returns our database collection
    chroma_client = chromadb.PersistentClient(path="chroma_db")  # Connects to our persistent database folder
    return chroma_client.get_or_create_collection("company_documents")  # Creates or opens our collection

collection = get_chroma_collection()  # Gets the cached collection


def read_docx(filepath):  # Extracts all text from a Word document
    doc = Document(filepath)  # Opens the .docx file
    full_text = []  # Collects each paragraph's text
    for paragraph in doc.paragraphs:  # Loops through every paragraph
        full_text.append(paragraph.text)  # Adds it to our list
    return "\n\n".join(full_text)  # Joins paragraphs with blank lines between them

def read_pdf(filepath):  # Extracts all text from a PDF file
    reader = PdfReader(filepath)  # Opens the PDF file
    full_text = []  # Collects each page's text
    for page in reader.pages:  # Loops through every page
        full_text.append(page.extract_text())  # Adds it to our list
    return "\n\n".join(full_text)  # Joins pages with blank lines between them

document_files = glob.glob("documents/*.txt") + glob.glob("documents/*.docx") + glob.glob("documents/*.pdf")  # Finds every .txt, .docx, and .pdf file inside the "documents" folder

all_chunks = []  # Will hold every chunk from every document, each remembering its source and ID

for filepath in document_files:  # Loops through each document's full file path
    if filepath.endswith(".docx"):  # Checks if this is a Word document
        text = read_docx(filepath)  # Uses our Word-reading function
    elif filepath.endswith(".pdf"):  # Checks if this is a PDF
        text = read_pdf(filepath)  # Uses our PDF-reading function
    else:  # Otherwise, assume it's a plain .txt file
        with open(filepath, "r") as file:  # Opens the text file normally
            text = file.read()  # Reads its contents

    display_name = os.path.basename(filepath)  # Extracts just the filename, dropping the folder path

    file_chunks = text.split("\n\n")  # Splits this document into its own chunks

    for chunk in file_chunks:  # Loops through each chunk from this specific file
        all_chunks.append({"id": len(all_chunks), "source": display_name, "text": chunk})  # Stores the chunk with a unique number, its clean filename, and its text

if collection.count() == 0:  # Only populate the database if it's currently empty
    chunk_ids = [f"chunk_{i}" for i in range(len(all_chunks))]  # Creates a unique ID for each chunk
    chunk_texts = [chunk["text"] for chunk in all_chunks]  # Extracts just the text
    chunk_metadata = [{"source": chunk["source"]} for chunk in all_chunks]  # Extracts just the source info

    collection.add(  # Adds everything to the database at once
        documents=chunk_texts,  # The chunk text
        ids=chunk_ids,  # Unique IDs
        metadatas=chunk_metadata  # Source file info
    )


my_email = "Adam@M365x13102857.onmicrosoft.com"  # The email address we send FROM
my_password = os.getenv("EMAIL_PASSWORD")  # Reads the EMAIL_PASSWORD value from .env

def send_email(subject, body):  # Our reusable "machine" — takes a subject and body as inputs
    to_email = st.session_state.get("user_email", "Adam@M365x13102857.onmicrosoft.com")  # Sends to the real signed-in user if known, otherwise falls back to the test address
    message = f"Subject: {subject}\n\n{body}"  # Combines subject + body into the format email servers expect

    server = smtplib.SMTP("smtp.office365.com", 587)  # Connects to Microsoft's outgoing mail server
    server.starttls()  # Upgrades the connection to an encrypted one
    server.login(my_email, my_password)  # Logs in with our stored credentials
    server.sendmail(my_email, to_email, message)  # Sends the email
    server.quit()  # Closes the connection cleanly

query_params = st.query_params  # Reads any parameters attached to the current URL

if "code" in query_params and "logged_in" not in st.session_state:  # Checks if Microsoft just redirected us back with a login code, and we haven't processed it yet
    auth_code = query_params["code"]  # Extracts the authorization code from the URL

    result = msal_web_app.acquire_token_by_authorization_code(  # Exchanges the code for a real access token
        auth_code,  # The code Microsoft gave us
        scopes=["User.Read"],  # Same permission scope as the request
        redirect_uri=REDIRECT_URI  # Must match exactly what we used to request the login
    )

    if "access_token" in result:  # Checks if the exchange succeeded
        st.session_state.logged_in = True  # Marks the user as logged in
        st.session_state.user_name = result["id_token_claims"]["name"]  # Stores their real name
        st.session_state.user_email = result["id_token_claims"]["preferred_username"]  # Stores their real email
        st.query_params.clear()  # Removes the code from the URL, so it isn't reused or shown
        st.rerun()  # Re-runs the app immediately, now showing the real chat interface

if "logged_in" not in st.session_state:  # Checks if we've already tracked login status this session
    st.session_state.logged_in = False  # If not, starts as "not logged in"

if not st.session_state.logged_in:  # If the user hasn't logged in yet
    st.title("AI Co-Worker Login")  # Shows a login-specific title
    password_attempt = st.text_input("Enter password:", type="password")  # Shows a password box (masked input, like real login forms)

    if st.button("Log in"):  # A button to submit the password
        if password_attempt == os.getenv("APP_PASSWORD"):  # Checks if it matches the real password from .env
            st.session_state.logged_in = True  # Marks the user as logged in
            st.rerun()  # Re-runs the app immediately, now showing the real chat interface
        else:  # Wrong password
            st.error("Incorrect password.")  # Shows a clear error message

    st.divider()  # Draws a visual line to separate the two login options

    if st.button("Sign in with Microsoft"):  # A new button offering real Entra ID login
        flow = msal_app.initiate_device_flow(scopes=["User.Read"])  # Starts the Microsoft sign-in process
        st.info(flow["message"])  # Shows the code and instructions to the user

        with st.spinner("Waiting for you to complete sign-in..."):  # Shows a spinner while we wait
            result = msal_app.acquire_token_by_device_flow(flow)  # Pauses here until sign-in completes (or times out)

        if "access_token" in result:  # Checks if sign-in succeeded
            st.session_state.logged_in = True  # Marks the user as logged in
            st.session_state.user_name = result["id_token_claims"]["name"]  # Stores their real name
            st.session_state.user_email = result["id_token_claims"]["preferred_username"]  # Stores their real email
            st.rerun()  # Re-runs the app immediately, showing the real chat interface
        else:  # If sign-in failed
            st.error("Microsoft sign-in failed. Please try again.")  # Shows an error

    st.divider()  # Another visual separator

    auth_url = msal_web_app.get_authorization_request_url(  # Builds the real Microsoft sign-in link
        scopes=["User.Read"],  # Same permission as before: read the signed-in user's own profile
        redirect_uri=REDIRECT_URI  # Where Microsoft should send the user back to afterward
    )
    button_style = "display:inline-block; padding:0.5em 1em; border:1px solid rgba(250,250,250,0.2); border-radius:0.5em; text-decoration:none; color:inherit;"  # Inline CSS that mimics Streamlit's default button appearance

    st.markdown(f'<a href="{auth_url}" target="_self" style="{button_style}">Sign in with Microsoft (Web)</a>', unsafe_allow_html=True)  # Shows a styled link that opens in the SAME tab
    st.stop()  # Stops the rest of the app from running until login succeeds

st.title("AI Co-Worker")  # Page title

if "user_name" in st.session_state:  # Checks if we know who's signed in (via Microsoft)
    st.caption(f"Signed in as {st.session_state.user_name} ({st.session_state.user_email})")  # Shows the real signed-in user
else:  # If they used the simple password instead
    st.caption("Signed in with app password")  # Shows a generic label

if st.button("Log out"):  # A button to end the session
    st.session_state.logged_in = False  # Marks the user as logged out
    st.session_state.pop("user_name", None)  # Clears their name, if it was set
    st.session_state.pop("user_email", None)  # Clears their email, if it was set
    st.rerun()  # Re-runs the app immediately, showing the login screen again

if "messages" not in st.session_state:  # Checks if we've already started a message history this session
    st.session_state.messages = []  # If not, creates an empty list to store messages in

for message in st.session_state.messages:  # Loops through every message we've stored so far
    with st.chat_message(message["role"]):  # Creates a chat bubble labeled as either "user" or "assistant"
        st.write(message["content"])  # Displays the message text inside that bubble

user_message = st.chat_input("What do you need help with?")  # Chat input box at the bottom

if user_message:  # Runs only when the user types something
    st.session_state.messages.append({"role": "user", "content": user_message})  # Stores the user's message with its role

    response = client.messages.create(  # Sends the full conversation to Claude for classification
        model="claude-sonnet-4-6",  # Which Claude model to use
        max_tokens=20,  # We only need one short word back
        system="Reply with ONLY one word: PASSWORD_RESET, CREATE_TICKET, SOFTWARE_ACCESS, KNOWLEDGE_QUESTION, or UNKNOWN, based on the user's most recent message and the conversation so far. Use KNOWLEDGE_QUESTION when the user is asking about company policies or information, rather than requesting an action.",  # Instructions that apply to the whole conversation
        messages=st.session_state.messages  # Sends the ENTIRE conversation history, not just the latest message
    )

    intent = response.content[0].text.strip()  # Extracts Claude's one-word classification

    if intent == "KNOWLEDGE_QUESTION":  # If this is a question, not an action request
        
        results = collection.query(  # Searches the vector database for the most relevant chunks
            query_texts=[user_message],  # The user's question (ChromaDB embeds this automatically)
            n_results=3  # How many top matches to return
        )

        filtered_context = "\n\n".join(  # Builds context from the top matches returned by ChromaDB
            f"[Source: {results['metadatas'][0][i]['source']}]\n{results['documents'][0][i]}"  # Pairs each chunk's text with its source
            for i in range(len(results["documents"][0]))  # Loops through however many results came back
        )

        answer_response = client.messages.create(  # Stage 2: asks Claude to answer using only the filtered context
            model="claude-sonnet-4-6",  # Which Claude model to use
            max_tokens=300,  # Maximum length of the answer
            system=f"Answer the user's question using ONLY the information in this context. If the answer isn't in the context, say you don't know. At the end of your answer, on a new line, state which source file(s) you used, like 'Source: filename.txt'.\n\nContext:\n{filtered_context}",  # Grounds the answer, requires citation
            messages=[
                {"role": "user", "content": user_message}  # The user's actual question
            ]
        )
        answer_text = answer_response.content[0].text  # Extracts the answer text
        st.session_state.messages.append({"role": "assistant", "content": answer_text})  # Shows the cited, grounded answer
        
    else:  # For actions or unknown requests, use our existing confirm-button flow
        st.session_state.messages.append({"role": "assistant", "content": f"I understood this as: {intent}"})  # Shows the classification
        st.session_state.pending_intent = intent  # Remembers it so we can show a confirm button

    st.rerun()  # Re-runs the app immediately so new messages appear right away

if "pending_intent" in st.session_state:  # Checks if we have a classification to confirm
    intent = st.session_state.pending_intent  # Retrieves the classification

    if intent == "UNKNOWN":  # If Claude couldn't match this to a known action
        st.info("Sorry, I don't know how to help with that request yet.")  # Shows a clear info message instead of a button
        del st.session_state.pending_intent  # Clears the pending action, since there's nothing to confirm
    elif st.button(f"Confirm intent: {intent}"):  # For known actions, shows a button to confirm
        
        if intent == "PASSWORD_RESET":  # If the classification is PASSWORD_RESET
            send_email("Password Reset Request", "Please reset my password.")  # Sends an email to IT
            st.session_state.messages.append({"role": "assistant", "content": "I've sent a password reset request to IT."})  # Confirms to the user

        elif intent == "CREATE_TICKET":  # If the classification is CREATE_TICKET
            send_email("New Ticket Request", "Please create a new support ticket.")  # Sends an email to IT
            st.session_state.messages.append({"role": "assistant", "content": "I've sent a request to create a new support ticket."})  # Confirms to the user

        elif intent == "SOFTWARE_ACCESS":  # If the classification is SOFTWARE_ACCESS
            send_email("Software Access Request", "Please grant me access to the requested software.")  # Sends an email to IT
            st.session_state.messages.append({"role": "assistant", "content": "I've sent a software access request to IT."})  # Confirms to the user

        else:  # If the classification is UNKNOWN
            st.session_state.messages.append({"role": "assistant", "content": "I'm not sure how to handle that request. Please contact IT directly."})  # Informs the user of uncertainty

        del st.session_state.pending_intent  # Clears the pending intent after confirmation
        
        st.rerun()  # Re-runs the app immediately so the new messages appear right away

