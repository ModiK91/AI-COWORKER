from docx import Document  # Imports the tool for reading Word (.docx) files
from pypdf import PdfReader  # Imports the tool for reading PDF files
from dotenv import load_dotenv  # Lets us read secrets from .env
import os  # Lets us access those loaded secrets
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude

def read_docx(filepath):  # A function that extracts all text from a Word document
    doc = Document(filepath)  # Opens the .docx file
    full_text = []  # Will collect each paragraph's text

    for paragraph in doc.paragraphs:  # Loops through every paragraph in the document
        full_text.append(paragraph.text)  # Adds this paragraph's text to our list

    return "\n\n".join(full_text)  # Joins all paragraphs together, separated by blank lines (matching our chunk-splitting style)


def read_pdf(filepath):  # A function that extracts all text from a PDF file
    reader = PdfReader(filepath)  # Opens the PDF file
    full_text = []  # Will collect each page's text

    for page in reader.pages:  # Loops through every page in the PDF
        full_text.append(page.extract_text())  # Extracts and adds this page's text to our list

    return "\n\n".join(full_text)  # Joins all pages together, separated by blank lines


load_dotenv()  # Loads ANTHROPIC_API_KEY from .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates our connection to Claude

#document_files = ["company_policy.txt", "it_security_policy.txt"]  # A list of every document we want to search across
document_files = ["documents/company_policy.txt", "documents/it_security_policy.txt"]  # A list of every document we want to search across, now inside the documents folder

all_chunks = []  # This will hold every chunk from every document, each remembering its source

for filename in document_files:  # Loops through each document file name
    with open(filename, "r") as file:  # Opens that specific file
        text = file.read()  # Reads its contents

    file_chunks = text.split("\n\n")  # Splits this document into its own chunks

    for chunk in file_chunks:  # Loops through each chunk from this specific file
        all_chunks.append({"id": len(all_chunks), "source": filename, "text": chunk})  # Stores the chunk with a unique number, its source, and its text
        
print(f"Found {len(all_chunks)} chunks across {len(document_files)} documents:")  # Shows how many chunks total, across how many files
for chunk in all_chunks:  # Loops through each chunk
    print(f"--- from {chunk['source']} ---")  # Shows which file this chunk came from
    print(chunk["text"])  # Prints the chunk's actual text

#question = "What is the password policy?"  # A test question that should match our NEW second document
#question = "What are the rules for remote work and password security?"  # A question spanning BOTH documents
question = "What is the VPN policy?"  # A question that should ONLY match one chunk, not the others

chunk_list_text = "\n\n".join(f"[{chunk['id']}] (from {chunk['source']}): {chunk['text']}" for chunk in all_chunks)  # Builds a numbered list of every chunk, for Claude to review

relevance_response = client.messages.create(  # Asks Claude which chunks are actually relevant to the question
    model="claude-sonnet-4-6",  # Which Claude model to use
    max_tokens=50,  # We only need a short list of numbers back
    system="You are a relevance-filtering tool, not a question-answering assistant. You will be shown a numbered list of text chunks and a question. Your ONLY job is to output the numbers of chunks relevant to the question, separated by commas (e.g. '0,3'). Do NOT answer the question. Do NOT explain. Output ONLY numbers and commas, or the word 'none'.",  # A much stricter instruction, explicitly forbidding Claude from answering
    messages=[
        {"role": "user", "content": f"Chunks:\n{chunk_list_text}\n\nWhich chunk numbers are relevant to this question: '{question}'? Remember: output ONLY numbers, nothing else."}  # Reinforces the instruction directly in the message too
    ]
)

relevant_ids_text = relevance_response.content[0].text.strip()  # Extracts Claude's reply (a list of numbers, or "none")
print(f"Claude says relevant chunks are: {relevant_ids_text}")  # Shows us what Claude decided, so we can verify it

if relevant_ids_text == "none":  # Handles the case where nothing was relevant
    relevant_ids = []  # No chunks to use
else:
    relevant_ids = [int(id) for id in relevant_ids_text.split(",")]  # Converts the text "0,3" into an actual list of numbers: [0, 3]

relevant_chunks = [chunk for chunk in all_chunks if chunk["id"] in relevant_ids]  # Filters all_chunks down to only the ones Claude flagged as relevant

context = "\n\n".join(f"[Source: {chunk['source']}]\n{chunk['text']}" for chunk in relevant_chunks)  # Builds context using ONLY the relevant chunks, not all of them

response = client.messages.create(  # Sends the question + context to Claude
    model="claude-sonnet-4-6",  # Which Claude model to use
    max_tokens=200,  # Maximum length of the answer
    system=f"Answer the user's question using ONLY the information in this context. If the answer isn't in the context, say you don't know. At the end of your answer, on a new line, state which source file(s) you used, like 'Source: filename.txt'.\n\nContext:\n{context}",  # Instructs Claude to stick to the facts AND cite its source
    messages=[
        {"role": "user", "content": question}  # The actual question being asked
    ]
)

print(response.content[0].text)  # Prints Claude's grounded answer
