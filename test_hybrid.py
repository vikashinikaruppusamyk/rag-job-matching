from vector_db import init_collection, embed_query
import re

sample_jd = """
Senior Backend Engineer with 5+ years of experience.
Expert in Python and FastAPI.
"""

collection = init_collection()

# Debug: Embed JD
print("Step 1: Embed JD")
jd_embedding = embed_query(sample_jd)
print(f"JD embedding size: {len(jd_embedding)}\n")

# Debug: Query ChromaDB directly
print("Step 2: Query ChromaDB directly")
print(f"Querying for top 10 results...")
results = collection.query(
    query_embeddings=[jd_embedding],
    n_results=10
)

print(f"Got {len(results['ids'][0])} results")
print(f"IDs: {results['ids'][0]}")
print(f"Distances: {results['distances'][0]}")
print(f"Metadata count: {len(results['metadatas'][0])}")

if results['metadatas'][0]:
    print(f"\nFirst 3 results:")
    for i in range(min(3, len(results['metadatas'][0]))):
        metadata = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        score = (1 - distance) * 100
        print(f"  {i+1}. {metadata.get('name', 'Unknown')}: distance={distance:.3f}, score={score:.1f}")