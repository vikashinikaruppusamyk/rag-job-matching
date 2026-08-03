import os
import json
import chromadb

def setup_persistent_db():
    """Setup ChromaDB with persistent storage."""
    
    # Create persistent client pointing to a folder
    db_path = './chroma_data'
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(
        name='resumes',
        metadata={"hnsw:space": "cosine"}
    )
    
    # Check if already populated
    count = collection.count()
    print(f"Collection has {count} embeddings")
    
    if count > 0:
        print("✓ Database already populated!")
        return client, collection
    
    # Load and store embeddings
    print("\nLoading embeddings from cache...")
    with open('embeddings_cache.json', 'r') as f:
        embeddings_data = json.load(f)
    
    print(f"Storing {len(embeddings_data)} embeddings...")
    
    for i, (doc_id, item) in enumerate(embeddings_data.items(), 1):
        try:
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
                print(f"  Stored {i}/{len(embeddings_data)}...")
        
        except Exception as e:
            print(f"Error storing {doc_id}: {e}")
    
    print(f"✓ Successfully stored {len(embeddings_data)} embeddings\n")
    return client, collection

if __name__ == '__main__':
    client, collection = setup_persistent_db()
    print(f"Final count: {collection.count()} embeddings")