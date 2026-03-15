import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# This simulates indexing enterprise documentation offline for the POC
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# A lightweight open-source embedding model
# For a production MLOps environment, we'd use OpenAI Embeddings or a hosted SentenceTransformer
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def initialize_vector_db():
    """
    Reads dummy enterprise data from the `data/` folder and indexes it.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Create a dummy enterprise document if it doesn't exist
    sample_doc_path = os.path.join(DATA_DIR, "company_policy.txt")
    if not os.path.exists(sample_doc_path):
        with open(sample_doc_path, "w") as f:
            f.write("Company Policy Overview:\n")
            f.write("1. Remote Work: Employees are allowed to remote work 3 days a week.\n")
            f.write("2. Hardware: Every engineer gets a MacBook Pro M3 Max upon joining.\n")
            f.write("3. PTO: Unlimited PTO is approved upon manager discretion, minimum 2 weeks required.\n")
            f.write("4. Server Architecture: All production ML models are deployed on KServe using AWS EKS clusters.\n")
            f.write("5. ML CI/CD: We use GitHub actions for all pipeline orchestration, and MLFlow for experiment tracking.\n")

    # Load the document
    loader = TextLoader(sample_doc_path)
    docs = loader.load()

    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)
    
    # Generate vector db store, saving to local disk
    print("Indexing documents into ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_function,
        persist_directory=DB_DIR
    )
    print("Indexing complete.")
    return vectorstore

def get_retriever():
    """Loads the existing vector database to answer queries."""
    # If the database doesn't exist yet, build it
    if not os.path.exists(DB_DIR):
        vectorstore = initialize_vector_db()
    else:
        vectorstore = Chroma(
            persist_directory=DB_DIR,
            embedding_function=embedding_function
        )
    return vectorstore.as_retriever(search_kwargs={"k": 2})

# Expose this as a LangChain Tool for the Agent
def retrieve_internal_document(query: str) -> str:
    """
    Retrieves internal company policies or enterprise MLOps architecture information.
    ALWAYS use this tool when asked about company policies, architecture, or internal guidelines.
    Args:
        query: The topic or question to search the internal knowledge base for.
    """
    retriever = get_retriever()
    matched_docs = retriever.invoke(query)
    
    if not matched_docs:
        return "No relevant internal enterprise information found for that query."
    
    # Combine the retrieved document content into a single string for the LLM
    context = "\n".join([doc.page_content for doc in matched_docs])
    return f"INTERNAL KNOWLEDGE BASE RESULT:\n{context}"

# Run once on boot to ensure the DB is ready
if __name__ == "__main__":
    initialize_vector_db()
