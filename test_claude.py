from dotenv import load_dotenv  # Lets us read secrets from .env
import os  # Lets us access those loaded secrets
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude

load_dotenv()  # Opens .env and loads EMAIL_PASSWORD and ANTHROPIC_API_KEY into memory

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates a "connection object" authenticated with your API key

response = client.messages.create(  # Sends a request to Claude and waits for a response
    model="claude-sonnet-4-6",  # Which Claude model to use
    max_tokens=100,  # The maximum length of Claude's reply (100 tokens is roughly 75 words)
    messages=[
        {"role": "user", "content": "A user typed: 'What time is the company holiday party?'. Reply with ONLY one word: PASSWORD_RESET, CREATE_TICKET, or UNKNOWN."}  # Asks Claude to classify the request into one of three fixed labels
    ]
)

print(response.content[0].text)  # Prints just the text part of Claude's reply