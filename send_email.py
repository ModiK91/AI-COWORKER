from dotenv import load_dotenv  # Imports the tool that can read secret values from our .env file
import os  # Python's built-in tool for reading values from the computer's environment (where dotenv places them)
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude

load_dotenv()  # This actually opens .env and loads its contents so we can use them
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates a connection to Claude, authenticated with our API key

import smtplib  # Python's built-in tool for sending emails (SMTP = the standard protocol for sending mail)

my_email = "Adam@M365x13102857.onmicrosoft.com"  # The email address we send FROM
my_password = os.getenv("EMAIL_PASSWORD")  # Reads the EMAIL_PASSWORD value we stored in .env, instead of typing it directly here

def send_email(subject, body):  # Our reusable "machine" — takes a subject and body as inputs
    to_email = "Adam@M365x13102857.onmicrosoft.com"  # Who receives the email (still yourself, for testing)
    message = f"Subject: {subject}\n\n{body}"  # Combines subject + body into the format email servers expect

    server = smtplib.SMTP("smtp.office365.com", 587)  # Connects to Microsoft's outgoing mail server
    server.starttls()  # Upgrades the connection to an encrypted one
    server.login(my_email, my_password)  # Logs in with our stored credentials
    server.sendmail(my_email, to_email, message)  # Sends the email
    server.quit()  # Closes the connection cleanly

    print("Email sent successfully!")  # Confirms it worked

while True:  # Repeats everything below forever, until we hit "exit()"
    # --- Simple decision logic: pretend a user typed a request ---
    #user_request = "reset my password"  # Imagine this text came from a user typing into a chat box
    #user_request = "order me a pizza"  # A request our AI Co-Worker doesn't know how to handle
    #user_request = "Can I get access to Photoshop for a project?"  # This simulates a message typed by a real user
    #user_request = input("What do you need help with? ")  # Pauses the script and waits for you to type a real request
    user_request = input("What do you need help with? (type 'exit' to quit) ")  # Pauses the script and waits for you to type a real request

    if user_request == "exit":  # Checks if the user wants to stop
        print("Goodbye!")  # Friendly closing message
        exit()  # Stops the script immediately, skipping everything below


    response = client.messages.create(  # Sends the user's request to Claude for classification
        model="claude-sonnet-4-6",  # Which Claude model to use
        max_tokens=20,  # We only need one short word back, so keep this small
        messages=[
        {"role": "user", "content": f"A user typed: '{user_request}'. Reply with ONLY one word: PASSWORD_RESET, CREATE_TICKET, SOFTWARE_ACCESS, or UNKNOWN."}  # Asks Claude to classify the request into one of four labels  # Asks Claude to classify the request, inserting the real user_request text
    ]
)

    intent = response.content[0].text.strip()  # Extracts just Claude's one-word answer, removing any extra spaces
    print(f"Claude classified this as: {intent}")  # Shows us what Claude decided, so we can verify it before acting

    if intent == "PASSWORD_RESET":  # Checks Claude's classification
        confirm = input("AI wants to send a Password Reset email. Type 'yes' to confirm: ")  # Waits for human approval
        if confirm == "yes":  # Only proceeds if the human typed exactly "yes"
            send_email("Password Reset Confirmation", "Your password has been reset by your AI Co-Worker.")  # Sends the reset email
        else:  # Any other typed response
            print("Action cancelled by user.")  # Confirms nothing was sent
    elif intent == "CREATE_TICKET":  # Checks Claude's classification for the ticket case
        confirm = input("AI wants to create a Support Ticket. Type 'yes' to confirm: ")  # Waits for human approval
        if confirm == "yes":  # Only proceeds if confirmed
            send_email("New Support Ticket Created", "A new IT support ticket has been created on your behalf.")  # Sends the ticket email
        else:
            print("Action cancelled by user.")  # Confirms nothing was sent
    elif intent == "SOFTWARE_ACCESS":  # Checks Claude's classification for software access
        confirm = input("AI wants to submit a Software Access request. Type 'yes' to confirm: ")  # Waits for human approval
        if confirm == "yes":  # Only proceeds if confirmed
            send_email("Software Access Request Submitted", "Your software access request has been submitted for approval.")  # Sends the software access email
        else:
            print("Action cancelled by user.")  # Confirms nothing was sent
    else:  # Covers UNKNOWN or any unexpected reply
        print("Sorry, I don't know how to handle that request yet.")  # Safely does nothing harmful
