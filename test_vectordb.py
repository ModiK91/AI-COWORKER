import glob  # For finding files in the documents folder
import os  # For extracting clean filenames
from docx import Document  # For reading Word files
from pypdf import PdfReader  # For reading PDF files

import chromadb  # Imports the vector database tool

client = chromadb.PersistentClient(path="chroma_db")  # Creates a database that saves permanently to a folder called "chroma_db"

collection = client.get_or_create_collection("company_documents")  # Creates (or opens, if it already exists) a "collection" — like a table just for our documents

def read_docx(filepath):  # Extracts all text from a Word document
    doc = Document(filepath)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return "\n\n".join(full_text)

def read_pdf(filepath):  # Extracts all text from a PDF file
    reader = PdfReader(filepath)
    full_text = []
    for page in reader.pages:
        full_text.append(page.extract_text())
    return "\n\n".join(full_text)

document_files = glob.glob("documents/*.txt") + glob.glob("documents/*.docx") + glob.glob("documents/*.pdf")  # Finds every document

all_chunks = []  # Will hold every chunk of text
chunk_ids = []  # ChromaDB requires a unique ID string for every entry
chunk_metadata = []  # Will hold the source filename for each chunk

for filepath in document_files:  # Loops through each document
    if filepath.endswith(".docx"):
        text = read_docx(filepath)
    elif filepath.endswith(".pdf"):
        text = read_pdf(filepath)
    else:
        with open(filepath, "r") as file:
            text = file.read()

    display_name = os.path.basename(filepath)  # Clean filename
    file_chunks = text.split("\n\n")  # Splits into chunks

    for chunk in file_chunks:  # Loops through each chunk
        chunk_id = f"chunk_{len(all_chunks)}"  # Creates a unique ID like "chunk_0", "chunk_1", etc.
        all_chunks.append(chunk)  # Stores the chunk text
        chunk_ids.append(chunk_id)  # Stores its ID
        chunk_metadata.append({"source": display_name})  # Stores which file it came from

print(f"Prepared {len(all_chunks)} chunks from {len(document_files)} documents")  # Confirms what we've loaded
if collection.count() == 0:  # Only adds chunks if the database is currently empty
    collection.add(  # Adds all our chunks to the vector database at once
        documents=all_chunks,  # The actual text of each chunk
        ids=chunk_ids,  # The unique ID for each chunk
        metadatas=chunk_metadata  # The source filename for each chunk
    )
    print(f"Added {collection.count()} chunks to the database")  # Confirms how many were added
else:  # If chunks already exist
    print(f"Database already has {collection.count()} chunks, skipping re-add")  # Confirms we skipped re-adding
    
results = collection.query(  # Searches the database for the most relevant chunks
    query_texts=["What is the VPN policy?"],  # The question we're asking (ChromaDB embeds this automatically)
    n_results=2  # How many top matches to return
)

print("Top matches:")  # Header for clarity
for i, doc in enumerate(results["documents"][0]):  # Loops through each returned chunk
    source = results["metadatas"][0][i]["source"]  # Gets that chunk's source file
    print(f"[{source}] {doc[:80]}...")  # Prints the source and a preview of the text