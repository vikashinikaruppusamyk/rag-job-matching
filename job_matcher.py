import json
from typing import List, Dict
from hybrid_matcher import hybrid_search, apply_must_have_filters
from vector_db import init_collection

def format_match_output(jd: str, matches: List[Dict]) -> Dict:
    """
    Format matches according to spec:
    {
        "job_description": "...",
        "top_matches": [
            {
                "candidate_name": "...",
                "resume_path": "resumes/...",
                "match_score": 92,
                "matched_skills": ["Python", "Machine Learning"],
                "relevant_excerpts": ["..."],
                "reasoning": "Strong match for ML experience..."
            }
        ]
    }
    """
    
    formatted_matches = []
    
    for match in matches[:10]:  # Top 10 only
        # Parse matched skills from metadata
        skills_str = match['metadata'].get('skills', '')
        all_skills = [s.strip().title() for s in skills_str.split(',')]
        
        # Keep only matched keywords as skills
        matched_skills = [s for s in all_skills if s.lower() in [kw.lower() for kw in match['matched_keywords']]]
        
        # Generate reasoning
        semantic = match['semantic_score']
        keyword = match['keyword_score']
        years = match['metadata'].get('years_exp', 0)
        
        if semantic > 70 and keyword > 80:
            reasoning = f"Excellent match: Strong semantic alignment ({semantic:.0f}) with all critical keywords ({keyword:.0f}). {years}+ years experience."
        elif semantic > 60 and keyword > 70:
            reasoning = f"Good match: Solid semantic fit ({semantic:.0f}) with most required keywords ({keyword:.0f}). {years} years experience."
        else:
            reasoning = f"Moderate match: Semantic score {semantic:.0f}, keyword coverage {keyword:.0f}. {years} years experience."
        
        formatted_matches.append({
            'candidate_name': match['candidate_name'],
            'resume_path': f"resumes/{match['metadata'].get('source', 'unknown')}",
            'match_score': match['match_score'],
            'matched_skills': matched_skills[:5],  # Top 5 skills
            'relevant_excerpts': [match['excerpt']],
            'reasoning': reasoning
        })
    
    return {
        'job_description': jd[:500] + '...' if len(jd) > 500 else jd,
        'top_matches': formatted_matches
    }

def run_job_matcher(jd: str, top_k: int = 10, output_file: str = None) -> Dict:
    """
    Complete job matching pipeline.
    
    Args:
        jd: Job description text
        top_k: Number of results to return
        output_file: Optional file to save JSON output
    
    Returns:
        Formatted output dict
    """
    
    print(f"\n{'='*70}")
    print(f"JOB MATCHER")
    print(f"{'='*70}\n")
    
    # Initialize collection
    collection = init_collection()
    
    # Run hybrid search
    print("Running hybrid search...")
    matches = hybrid_search(collection, jd, top_k=top_k)
    
    # Apply filters
    print("Applying must-have filters...")
    filtered_matches = apply_must_have_filters(matches, jd)
    
    # Format output
    output = format_match_output(jd, filtered_matches)
    
    # Print results
    print(f"\n{'='*70}")
    print(f"TOP {len(output['top_matches'])} MATCHES")
    print(f"{'='*70}\n")
    
    for i, match in enumerate(output['top_matches'], 1):
        print(f"{i}. {match['candidate_name']} | Score: {match['match_score']}/100")
        print(f"   Skills: {', '.join(match['matched_skills'])}")
        print(f"   Reasoning: {match['reasoning']}\n")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"✓ Output saved to {output_file}\n")
    
    return output

# ===== TEST =====

if __name__ == '__main__':
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
    """
    
    # Run matcher and save output
    output = run_job_matcher(sample_jd, top_k=10, output_file='output_sample.json')
    
    # Also print JSON
    print(f"{'='*70}")
    print(f"JSON OUTPUT")
    print(f"{'='*70}\n")
    print(json.dumps(output, indent=2))