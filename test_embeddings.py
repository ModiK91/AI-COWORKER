from dotenv import load_dotenv  # Lets us read secrets from .env
import os  # Lets us access those loaded secrets
from anthropic import Anthropic  # Imports the tool that lets us talk to Claude

load_dotenv()  # Loads ANTHROPIC_API_KEY from .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # Creates our connection to Claude

from sentence_transformers import SentenceTransformer  # Imports the tool that converts text into vectors (lists of numbers)

model = SentenceTransformer("all-MiniLM-L6-v2")  # Loads a small, well-tested embedding model (downloads it once, then reuses it)

sentence = "The VPN requires IT-issued credentials."  # A test sentence to convert

vector = model.encode(sentence)  # Converts the sentence into a vector (a list of numbers representing its meaning)

print(f"Vector length: {len(vector)}")  # Shows how many numbers make up this vector
print(f"First 10 numbers: {vector[:10]}")  # Shows just a small preview, since the full vector is long

from sentence_transformers import util  # Imports a helper tool for comparing vectors

sentence_a = "The VPN requires IT-issued credentials."  # Our original sentence
sentence_b = "You need credentials from IT to use the VPN."  # Same meaning, different wording
sentence_c = "Expense reports are processed within 10 business days."  # A completely unrelated sentence

vector_a = model.encode(sentence_a)  # Converts sentence A to a vector
vector_b = model.encode(sentence_b)  # Converts sentence B to a vector
vector_c = model.encode(sentence_c)  # Converts sentence C to a vector

similarity_ab = util.cos_sim(vector_a, vector_b)  # Measures how "close" A and B are (1.0 = identical meaning, 0 = unrelated)
similarity_ac = util.cos_sim(vector_a, vector_c)  # Measures how "close" A and C are

print(f"Similarity between A and B (similar meaning): {similarity_ab.item():.4f}")  # Prints the similarity score for A vs B
print(f"Similarity between A and C (unrelated): {similarity_ac.item():.4f}")  # Prints the similarity score for A vs C

#Load document chunks and embed them all
import glob  # For finding files in the documents folder
import os  # For extracting clean filenames

document_files = glob.glob("documents/*.txt")  # For this test, we'll start with just the .txt files

all_chunks = []  # Will hold every chunk of text

for filepath in document_files:  # Loops through each document
    with open(filepath, "r") as file:  # Opens the file
        text = file.read()  # Reads its contents

    display_name = os.path.basename(filepath)  # Gets just the filename
    file_chunks = text.split("\n\n")  # Splits into chunks

    for chunk in file_chunks:  # Loops through each chunk
        all_chunks.append({"source": display_name, "text": chunk})  # Stores it

print(f"Loaded {len(all_chunks)} chunks total")  # Confirms how many chunks we have

chunk_texts = [chunk["text"] for chunk in all_chunks]  # Extracts just the text from each chunk, as a plain list
chunk_vectors = model.encode(chunk_texts)  # Converts EVERY chunk into a vector, all at once

print(f"Created {len(chunk_vectors)} vectors, each with {len(chunk_vectors[0])} numbers")  # Confirms the embeddings were created

#Search chunks using vector similarity
question = "What is the VPN policy?"  # A test question

question_vector = model.encode(question)  # Converts the question into a vector, using the same model

similarities = util.cos_sim(question_vector, chunk_vectors)[0]  # Compares the question's vector against EVERY chunk vector at once

#for i, score in enumerate(similarities):  # Loops through each chunk's similarity score
    #print(f"{score:.4f} — [{all_chunks[i]['source']}] {all_chunks[i]['text'][:60]}...")  # Prints the score alongside a preview of the chunk

import numpy as np  # A math library, used here just to help sort scores easily

top_indices = np.argsort(-similarities)[:2]  # Finds the positions of the 2 highest-scoring chunks (the minus sign sorts highest-first)

print("Top matching chunks:")  # Header for clarity
for i in top_indices:  # Loops through just the top 2 positions
    print(f"{similarities[i]:.4f} — [{all_chunks[i]['source']}] {all_chunks[i]['text']}")  # Prints the full chunk text for the top matches

#Answer the question using the top embedded chunks
top_chunks_text = "\n\n".join(f"[Source: {all_chunks[i]['source']}]\n{all_chunks[i]['text']}" for i in top_indices)  # Builds context from only the top embedded matches

answer_response = client.messages.create(  # Asks Claude to answer using this vector-retrieved context
    model="claude-sonnet-4-6",  # Which Claude model to use
    max_tokens=300,  # Maximum length of the answer
    system=f"Answer the user's question using ONLY the information in this context. If the answer isn't in the context, say you don't know. At the end of your answer, state which source file(s) you used.\n\nContext:\n{top_chunks_text}",  # Grounds the answer, requires citation
    messages=[
        {"role": "user", "content": question}  # The actual question
    ]
)

print("\nFinal Answer:")  # Header for clarity
print(answer_response.content[0].text)  # Prints Claude's grounded answer