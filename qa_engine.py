# This module loads a knowledge base from documents, creates a retrieval-based
# QA chain, and provides a function to answer questions based on the documents.

import os
from dotenv import load_dotenv
import pprint  # For nicely printing dictionaries

# LangChain and related components
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

# --- 1. CONFIGURATION ---
# Load environment variables from a .env file (for the GOOGLE_API_KEY)
load_dotenv()

# Define constants for file paths and model names to make them easy to change
DB_PATH = "chroma_db"
DATA_PATH = "docs/"
MODEL_NAME = "gemini-1.5-flash-latest"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# --- 2. CORE FUNCTIONS ---

def load_vector_db():
    """
    Loads the vector database from the specified path. If the database
    doesn't exist, it builds a new one from the documents in the DATA_PATH.
    Returns:
        Chroma: The loaded or newly created vector database object.
    """
    # Initialize the embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )

    # Check if the database directory exists
    if not os.path.exists(DB_PATH):
        print(
            f"Knowledge base not found at '{DB_PATH}'. Building a new one...")

        # Load all PDF documents from the data path
        documents = []
        for file in os.listdir(DATA_PATH):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(DATA_PATH, file)
                print(f"Loading document: {pdf_path}")
                loader = PyPDFLoader(pdf_path)
                documents.extend(loader.load())

        # Split documents into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(documents)

        # Create the vector database and persist it to disk
        print(f"Creating embeddings and building the knowledge base... (This may take a moment)")
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=DB_PATH
        )
        print("New knowledge base built successfully!")
    else:
        # Load the existing database from disk
        print(f"Loading existing knowledge base from '{DB_PATH}'...")
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embedding_model
        )

    return vector_db


def create_qa_chain(vector_db):
    """
    Creates and returns the Question-Answering chain.
    Args:
        vector_db (Chroma): The vector database to retrieve context from.
    Returns:
        RetrievalQA: The configured QA chain object.
    """
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.2,
        convert_system_message_to_human=True
    )

    # Create a retriever from the vector database
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # Create and return the final QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain


def get_answer(query: str) -> dict:
    """
    The main public function for the QA engine. It takes a text query and
    returns a dictionary with the answer and source documents.
    Args:
        query (str): The question to be answered.
    Returns:
        dict: A dictionary containing the 'answer' and 'sources'.
    """
    print(f"\nReceived query: '{query}'")
    vector_db = load_vector_db()
    qa_chain = create_qa_chain(vector_db)

    print("Searching for an answer in the knowledge base...")
    result = qa_chain.invoke({"query": query})

    # Format the source documents for a cleaner output
    sources = []
    for doc in result.get("source_documents", []):
        sources.append({
            "source": os.path.basename(doc.metadata.get('source', 'N/A')),
            "page": doc.metadata.get('page', 'N/A'),
            "content_snippet": doc.page_content[:250] + "..."
        })

    return {
        "answer": result.get("result", "No answer found."),
        "sources": sources
    }


# 3. EXAMPLE USAGE BLOCK ---

if __name__ == '__main__':
    # Prompt the user to enter the question manually.
    # This simulates receiving the transcribed text from Ricky's module.
    question = input(
        "\nPlease run Ricky's script, speak your question, and paste the transcribed text here:\n> ")

    # Check if the user provided any input
    if question and question.strip():
        # Get the answer from your engine
        answer_data = get_answer(question.strip())

        # Print the final result in a clean format using pprint
        print("\n" + "="*50)
        print("      --- ANSWER FROM KNOWLEDGE BASE ---")
        print("="*50)
        pprint.pprint(answer_data)
        print("="*50)
    else:
        print("\nNo question was provided. Exiting.")
