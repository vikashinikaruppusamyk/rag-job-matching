import os
import json
import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Use persistent client instead of in-memory
db_path = './chroma_data'
os.makedirs(db_path, exist_ok=True)
db_client = chromadb.PersistentClient(path=db_path)

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def init_collection(collection_name: str = 'resumes'):
    """Initialize or get ChromaDB collection (persistent)."""
    collection = db_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def embed_query(query: str) -> list:
    """Embed query using OpenAI (same as resumes)."""
    response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=query
    )
    return response.data[0].embedding

def test_retrieval(collection, query: str, top_k: int = 5):
    """Test retrieval with a sample query."""
    print(f"Query: {query}\n")
    
    # Embed the query using OpenAI (same model as resumes)
    query_embedding = embed_query(query)
    
    # Query ChromaDB with the embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    print(f"Top {top_k} matches:\n")
    
    for i, (doc_id, distance, metadata, document) in enumerate(zip(
        results['ids'][0],
        results['distances'][0],
        results['metadatas'][0],
        results['documents'][0]
    ), 1):
        # Convert distance to similarity score (0-100)
        similarity = max(0, (1 - distance) * 100)
        
        print(f"{i}. {metadata['name']} | {metadata['years_exp']} years | Score: {similarity:.1f}")
        print(f"   Section: {metadata['section']}")
        print(f"   Skills: {metadata['skills'][:60]}...")
        print(f"   Excerpt: {document[:80]}...\n")

if __name__ == '__main__':
    print("=" * 60)
    print("TESTING PERSISTENT CHROMADB")
    print("=" * 60 + "\n")
    
    collection = init_collection()
    count = collection.count()
    print(f"Collection has {count} embeddings\n")
    
    # Test retrieval
    print("=" * 60)
    print("RETRIEVAL TEST")
    print("=" * 60 + "\n")
    test_retrieval(collection, "Python backend engineer with 5+ years experience", top_k=5)