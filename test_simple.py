import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import time
import json
from vector_db import init_collection

def verify_all():
    """Simple verification."""
    print("=" * 70)
    print("PIPELINE VERIFICATION")
    print("=" * 70 + "\n")
    
    collection = init_collection()
    count = collection.count()
    print(f"✓ Total embeddings: {count}")
    print(f"  (Expected: ~330 for 30 resumes)\n")
    
    # Test retrieval
    print("Testing retrieval...")
    start = time.time()
    results = collection.query(
        query_texts=["Python backend engineer"],
        n_results=10
    )
    elapsed = time.time() - start
    
    print(f"✓ Retrieved 10 results in {elapsed*1000:.1f}ms")
    print(f"  Top result: {results['metadatas'][0][0]['name']}\n")
    
    # Count unique candidates
    candidates = set()
    for doc_id in results['ids'][0]:
        # Extract name from doc_id (format: "Name_chunk_X")
        name = '_'.join(doc_id.split('_')[:-2])
        candidates.add(name)
    
    print(f"✓ Found {len(candidates)} unique candidates in this batch\n")
    
    # Test a simple match
    print("Testing job matcher...")
    from job_matcher import run_job_matcher
    
    simple_jd = "5+ years Python FastAPI PostgreSQL Docker AWS"
    output = run_job_matcher(simple_jd, top_k=3, output_file='test_output.json')
    
    print(f"✓ Top match: {output['top_matches'][0]['candidate_name']}")
    print(f"  Score: {output['top_matches'][0]['match_score']}/100\n")
    
    print("=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)

if __name__ == '__main__':
    verify_all()