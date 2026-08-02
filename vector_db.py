import os
import json
import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize clients
db_client = chromadb.Client()
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def init_collection(collection_name: str = 'resumes'):
    """Initialize or get ChromaDB collection."""
    collection = db_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def store_embeddings_in_db(cache_file: str = 'embeddings_cache.json', collection_name: str = 'resumes'):
    """Load embeddings from cache and store in ChromaDB."""
    
    collection = init_collection(collection_name)
    
    # Load embeddings from cache
    with open(cache_file, 'r') as f:
        embeddings_data = json.load(f)
    
    print(f"Storing {len(embeddings_data)} embeddings in ChromaDB...\n")
    
    # Store each embedding
    for i, (doc_id, item) in enumerate(embeddings_data.items(), 1):
        try:
            # Get source, default to empty string if not present
            source = item['metadata'].get('source', '')
            
            collection.add(
                ids=[doc_id],
                embeddings=[item['embedding']],
                documents=[item['text']],
                metadatas=[{
                    'name': item['metadata']['name'],
                    'years_exp': item['metadata']['years_exp'],
                    'skills': ', '.join(item['metadata']['skills']),
                    'section': item['section'],
                    'source': source
                }]
            )
            
            if i % 50 == 0:
                print(f"  Stored {i}/{len(embeddings_data)} embeddings...")
        
        except Exception as e:
            print(f"Error storing {doc_id}: {e}")
    
    print(f"\n✓ Successfully stored {len(embeddings_data)} embeddings in ChromaDB\n")
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
    print("CHROMADB SETUP & RETRIEVAL TEST")
    print("=" * 60 + "\n")
    
    # Store embeddings
    collection = store_embeddings_in_db()
    
    # Test retrieval with sample queries
    print("=" * 60)
    print("RETRIEVAL TEST 1: Backend Engineer")
    print("=" * 60 + "\n")
    test_retrieval(collection, "Python backend engineer with 5+ years experience", top_k=5)
    
    print("=" * 60)
    print("RETRIEVAL TEST 2: ML Engineer")
    print("=" * 60 + "\n")
    test_retrieval(collection, "Machine learning engineer with TensorFlow and deep learning", top_k=5)
    
    print("=" * 60)
    print("RETRIEVAL TEST 3: DevOps Engineer")
    print("=" * 60 + "\n")
    test_retrieval(collection, "DevOps engineer with Kubernetes and Docker experience", top_k=5)
    
    print("=" * 60)
    print("✓ ChromaDB setup complete!")
    print("=" * 60)