from dotenv import load_dotenv  # Lets us read secrets from .env
import os  # Lets us access those loaded secrets
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude

load_dotenv()  # Loads ANTHROPIC_API_KEY from .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates our connection to Claude

with open("company_policy.txt", "r") as file:  # Opens our test document in "read" mode
    document_text = file.read()  # Reads the entire file's contents into one big text string

print(document_text)  # Just prints it out, to confirm we read it correctly

chunks = document_text.split("\n\n")  # Splits the text into a list, breaking wherever there's a blank line between paragraphs

print(f"Found {len(chunks)} chunks:")  # Shows how many chunks we ended up with
for chunk in chunks:  # Loops through each chunk
    print("---")  # A visual divider between chunks
    print(chunk)  # Prints the chunk's text

    #question = "How does VPN access work?"  # A test question to search for
    question = "What is the company's policy on parental leave?"  # A question NOT covered in our document

context = "\n\n".join(chunks)  # Rejoins all chunks into one block of text, to send as context to Claude

response = client.messages.create(  # Sends the question + context to Claude
    model="claude-sonnet-4-6",  # Which Claude model to use
    max_tokens=200,  # Maximum length of the answer
    system=f"Answer the user's question using ONLY the information in this context. If the answer isn't in the context, say you don't know.\n\nContext:\n{context}",  # Instructs Claude to stick to the provided facts only
    messages=[
        {"role": "user", "content": question}  # The actual question being asked
    ]
)

print(response.content[0].text)  # Prints Claude's grounded answer