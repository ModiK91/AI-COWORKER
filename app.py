import streamlit as st  # Imports Streamlit

from dotenv import load_dotenv  # Lets us read secrets from .env
import os  # Lets us access those loaded secrets
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude

import smtplib  # Python's built-in tool for sending emails

load_dotenv()  # Loads ANTHROPIC_API_KEY from .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates our connection to Claude

with open("company_policy.txt", "r") as file:  # Opens our company document
    document_text = file.read()  # Reads its entire contents

chunks = document_text.split("\n\n")  # Splits it into separate topic chunks
context = "\n\n".join(chunks)  # Rejoins them into one context block to hand to Claude when needed

my_email = "Adam@M365x13102857.onmicrosoft.com"  # The email address we send FROM
my_password = os.getenv("EMAIL_PASSWORD")  # Reads the EMAIL_PASSWORD value from .env

def send_email(subject, body):  # Our reusable "machine" — takes a subject and body as inputs
    to_email = "Adam@M365x13102857.onmicrosoft.com"  # Who receives the email (yourself, for testing)
    message = f"Subject: {subject}\n\n{body}"  # Combines subject + body into the format email servers expect

    server = smtplib.SMTP("smtp.office365.com", 587)  # Connects to Microsoft's outgoing mail server
    server.starttls()  # Upgrades the connection to an encrypted one
    server.login(my_email, my_password)  # Logs in with our stored credentials
    server.sendmail(my_email, to_email, message)  # Sends the email
    server.quit()  # Closes the connection cleanly

st.title("AI Co-Worker")  # Page title

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
        answer_response = client.messages.create(  # Asks Claude to answer using our document as context
            model="claude-sonnet-4-6",  # Which Claude model to use
            max_tokens=300,  # Maximum length of the answer
            system=f"Answer the user's question using ONLY the information in this context. If the answer isn't in the context, say you don't know.\n\nContext:\n{context}",  # Grounds Claude's answer in our document
            messages=[
                {"role": "user", "content": user_message}  # The user's actual question
            ]
        )
        answer_text = answer_response.content[0].text  # Extracts the answer text
        st.session_state.messages.append({"role": "assistant", "content": answer_text})  # Shows the answer directly, no confirm button needed
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

