import re
from typing import List, Dict, Tuple
from openai import OpenAI
from vector_db import embed_query
import os
from dotenv import load_dotenv

load_dotenv()

def extract_jd_keywords(jd: str) -> List[str]:
    """
    Extract critical keywords from job description.
    Looks for: skills, experience levels, tools, etc.
    """
    keywords = []
    
    # Programming languages
    languages = ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'php', 'ruby', 'kotlin', 'scala']
    
    # Frameworks
    frameworks = ['react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'node', 'express', 'nextjs']
    
    # Databases
    databases = ['postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb']
    
    # Cloud/DevOps
    devops = ['aws', 'gcp', 'azure', 'docker', 'kubernetes', 'k8s', 'terraform', 'jenkins', 'gitlab', 'github']
    
    # ML/Data
    ml_tools = ['tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'spark', 'hadoop']
    
    jd_lower = jd.lower()
    
    all_keywords = languages + frameworks + databases + devops + ml_tools
    
    for keyword in all_keywords:
        if re.search(r'\b' + keyword + r'\b', jd_lower):
            keywords.append(keyword.lower())
    
    return list(set(keywords))

def keyword_match_score(resume_text: str, metadata: Dict, jd_keywords: List[str]) -> float:
    """
    Score based on how many JD keywords appear in resume.
    Returns 0-1 score.
    """
    if not jd_keywords:
        return 0.5  # neutral if no keywords
    
    # Combine resume text + metadata for searching
    resume_combined = (resume_text + ' ' + ' '.join(str(v) for v in metadata.values())).lower()
    
    # Count matches
    matches = 0
    for keyword in jd_keywords:
        if re.search(r'\b' + keyword + r'\b', resume_combined):
            matches += 1
    
    # Score as percentage of keywords found
    score = matches / len(jd_keywords)
    return score

def hybrid_search(
    collection,
    jd: str,
    top_k: int = 10,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> List[Dict]:
    """
    Hybrid search combining semantic similarity + keyword matching.
    
    Args:
        collection: ChromaDB collection
        jd: Job description text
        top_k: Number of results to return
        semantic_weight: Weight for semantic similarity (0-1)
        keyword_weight: Weight for keyword matching (0-1)
    
    Returns:
        List of matched candidates with scores (0-100)
    """
    
    print(f"Extracting keywords from JD...")
    jd_keywords = extract_jd_keywords(jd)
    print(f"Found {len(jd_keywords)} keywords: {', '.join(jd_keywords[:10])}{'...' if len(jd_keywords) > 10 else ''}\n")
    
    # Embed JD using OpenAI
    print(f"Embedding JD...")
    jd_embedding = embed_query(jd)
    
    # Get semantic search results (get more than top_k to rerank)
    print(f"Querying ChromaDB for top-{top_k * 2} semantic matches...\n")
    semantic_results = collection.query(
        query_embeddings=[jd_embedding],
        n_results=min(top_k * 2, 100)  # Get 2x to rerank by hybrid score
    )
    
    # Rerank using hybrid score
    scored_results = []
    seen_candidates = set()  # Avoid duplicates from different chunks
    
    for i, doc_id in enumerate(semantic_results['ids'][0]):
        metadata = semantic_results['metadatas'][0][i]
        candidate_name = metadata.get('name', 'Unknown')
        
        # Skip if we already have this candidate
        if candidate_name in seen_candidates:
            continue
        seen_candidates.add(candidate_name)
        
        # Semantic score (0-1, where 1 = perfect match)
        semantic_distance = semantic_results['distances'][0][i]
        semantic_score = max(0, 1 - semantic_distance)  # Convert distance to similarity
        
        # Keyword score (0-1)
        resume_text = semantic_results['documents'][0][i]
        keyword_score = keyword_match_score(resume_text, metadata, jd_keywords)
        
        # Hybrid score (weighted combination)
        hybrid_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)
        
        # Convert to 0-100 scale
        final_score = hybrid_score * 100
        
        scored_results.append({
            'doc_id': doc_id,
            'candidate_name': candidate_name,
            'match_score': round(final_score, 1),
            'semantic_score': round(semantic_score * 100, 1),
            'keyword_score': round(keyword_score * 100, 1),
            'matched_keywords': [kw for kw in jd_keywords if re.search(r'\b' + kw + r'\b', (resume_text + ' ' + ' '.join(str(v) for v in metadata.values())).lower())],
            'excerpt': resume_text[:120] + '...',
            'metadata': metadata
        })
    
    # Sort by hybrid score (descending) and return top-k
    scored_results.sort(key=lambda x: x['match_score'], reverse=True)
    return scored_results[:top_k]

def apply_must_have_filters(matches: List[Dict], jd: str) -> List[Dict]:
    """
    Filter out candidates that don't meet must-have requirements.
    Extracts must-haves from JD (e.g., "5+ years", "must know Python").
    """
    filtered = []
    
    # Check experience requirement (e.g., "5+ years")
    exp_match = re.search(r'(\d+)\+?\s*years?', jd.lower())
    if exp_match:
        required_years = int(exp_match.group(1))
        print(f"Must-have: {required_years}+ years experience\n")
        
        for match in matches:
            candidate_years = match['metadata'].get('years_exp', 0)
            if candidate_years >= required_years:
                filtered.append(match)
            else:
                print(f"  ✗ {match['candidate_name']}: only {candidate_years} years (filtered out)")
    else:
        filtered = matches
    
    return filtered if filtered else matches  # If all filtered, return all

# ===== TEST =====

if __name__ == '__main__':
    from vector_db import init_collection
    
    # Test with a sample JD
    sample_jd = """
    Senior Backend Engineer
    
    We are looking for a Senior Backend Engineer with 5+ years of experience.
    
    Requirements:
    - 5+ years of backend development experience
    - Expert in Python and FastAPI
    - Strong knowledge of PostgreSQL and Redis
    - Experience with Docker and Kubernetes
    - AWS cloud experience is a must
    - REST API design and microservices architecture
    
    Nice to have:
    - GraphQL experience
    - Experience with Terraform
    - Machine Learning background
    """
    
    print("=" * 70)
    print("HYBRID SEARCH TEST")
    print("=" * 70 + "\n")
    
    # Load collection
    collection = init_collection()
    
    # Run hybrid search
    matches = hybrid_search(collection, sample_jd, top_k=10)
    
    # Apply filters
    print("=" * 70)
    print("APPLYING MUST-HAVE FILTERS")
    print("=" * 70 + "\n")
    filtered_matches = apply_must_have_filters(matches, sample_jd)
    
    print("\n" + "=" * 70)
    print("TOP 10 MATCHES (After Filtering)")
    print("=" * 70 + "\n")
    
    for i, match in enumerate(filtered_matches[:10], 1):
        print(f"{i}. {match['candidate_name']} | {match['metadata']['years_exp']} years | Score: {match['match_score']}")
        print(f"   Semantic: {match['semantic_score']} | Keyword: {match['keyword_score']}")
        print(f"   Matched keywords: {', '.join(match['matched_keywords'][:5])}")
        print(f"   Excerpt: {match['excerpt']}\n")