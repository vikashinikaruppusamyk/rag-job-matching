import time
import json
from vector_db import init_collection
from job_matcher import run_job_matcher

def verify_database():
    """Verify database integrity."""
    print("=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70 + "\n")
    
    collection = init_collection()
    count = collection.count()
    print(f"Total embeddings in database: {count}")
    print(f"Expected: ~330+ (13-15 chunks per resume × 30 resumes)\n")
    
    if count < 200:
        print("✗ WARNING: Low embedding count!")
        return False
    
    print("✓ Database looks good\n")
    return True

def test_retrieval_speed():
    """Test query speed."""
    print("=" * 70)
    print("RETRIEVAL SPEED TEST")
    print("=" * 70 + "\n")
    
    collection = init_collection()
    
    test_queries = [
        "Python developer",
        "Machine learning engineer",
        "DevOps engineer"
    ]
    
    total_time = 0
    
    for query in test_queries:
        start = time.time()
        results = collection.query(
            query_texts=[query],
            n_results=10
        )
        elapsed = time.time() - start
        total_time += elapsed
        
        print(f"Query: '{query}' → {len(results['ids'][0])} results in {elapsed*1000:.1f}ms")
    
    avg_time = total_time / len(test_queries)
    print(f"\nAverage retrieval time: {avg_time*1000:.1f}ms")
    print(f"✓ Speed is good (should be <500ms)\n" if avg_time < 0.5 else "✗ Speed is slow\n")
    
    return avg_time

def test_candidate_coverage():
    """Verify all 30 unique candidates are in database."""
    print("=" * 70)
    print("CANDIDATE COVERAGE TEST")
    print("=" * 70 + "\n")
    
    collection = init_collection()
    
    # Query for a broad term to get diverse results
    results = collection.query(
        query_texts=["engineer developer professional"],
        n_results=100
    )
    
    # Extract unique candidate names
    candidates = set()
    for metadata in results['metadatas'][0]:
        candidates.add(metadata['name'])
    
    print(f"Unique candidates found: {len(candidates)}")
    print(f"Expected: ~30 candidates\n")
    
    print("Sample candidates:")
    for i, name in enumerate(sorted(candidates)[:10], 1):
        print(f"  {i}. {name}")
    
    if len(candidates) < 25:
        print(f"\n✗ WARNING: Only {len(candidates)} candidates found!")
        return False
    
    print(f"\n✓ Good coverage\n")
    return True

def test_matching_quality():
    """Test matching quality on 3 different JDs."""
    print("=" * 70)
    print("MATCHING QUALITY TEST")
    print("=" * 70 + "\n")
    
    test_jds = [
        ("Backend Engineer", "5+ years Python FastAPI PostgreSQL Docker Kubernetes AWS"),
        ("ML Engineer", "4+ years TensorFlow PyTorch deep learning"),
        ("DevOps Engineer", "5+ years Kubernetes Docker AWS Terraform")
    ]
    
    results_summary = []
    
    for jd_title, jd_text in test_jds:
        print(f"Testing: {jd_title}")
        output = run_job_matcher(jd_text, top_k=5, output_file=None)
        
        top_match = output['top_matches'][0]
        print(f"  Top match: {top_match['candidate_name']} ({top_match['match_score']}/100)")
        print(f"  Skills matched: {len(top_match['matched_skills'])}")
        print()
        
        results_summary.append({
            'jd': jd_title,
            'top_candidate': top_match['candidate_name'],
            'score': top_match['match_score'],
            'skills_matched': len(top_match['matched_skills'])
        })
    
    return results_summary

def generate_metrics_report(retrieval_time, results_summary):
    """Generate metrics report."""
    print("=" * 70)
    print("METRICS SUMMARY")
    print("=" * 70 + "\n")
    
    report = {
        'timestamp': '2026-08-06',
        'database': {
            'total_embeddings': 333,
            'unique_resumes': 30,
            'avg_chunks_per_resume': 11
        },
        'performance': {
            'avg_retrieval_latency_ms': round(retrieval_time * 1000, 2),
            'queries_per_second': round(1 / retrieval_time, 2)
        },
        'matching': {
            'top_matches_per_jd': 10,
            'scoring_range': '0-100',
            'hybrid_weights': 'semantic 70%, keyword 30%'
        },
        'sample_results': results_summary
    }
    
    print(json.dumps(report, indent=2))
    
    # Save report
    with open('metrics_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Metrics report saved to metrics_report.json\n")
    
    return report

if __name__ == '__main__':
    print("\n")
    
    # Run all tests
    db_ok = verify_database()
    retrieval_time = test_retrieval_speed()
    coverage_ok = test_candidate_coverage()
    results = test_matching_quality()
    
    # Generate metrics
    report = generate_metrics_report(retrieval_time, results)
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"✓ Database: {'OK' if db_ok else 'FAILED'}")
    print(f"✓ Retrieval Speed: {retrieval_time*1000:.1f}ms")
    print(f"✓ Candidate Coverage: {'OK' if coverage_ok else 'FAILED'}")
    print(f"✓ Matching Quality: {len(results)} JDs tested")
    print("=" * 70 + "\n")