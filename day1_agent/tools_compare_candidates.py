"""
Candidate Comparison Tool
Uses Claude API to provide intelligent head-to-head comparisons between candidates.
"""

import json
from anthropic import Anthropic
from state_schema import CandidateMatch, ExtractedJD


client = Anthropic()


def compare_candidates(
    candidates: list[CandidateMatch],
    jd_requirements: ExtractedJD,
    comparison_type: str = "brief"
) -> dict:
    """
    Compare multiple candidates side-by-side using Claude API.
    
    Args:
        candidates: List of candidates to compare
        jd_requirements: The job requirements context
        comparison_type: "brief" (summary) or "detailed" (deep analysis)
    
    Returns:
        Dictionary with comparison results
    """
    
    # Format candidates for Claude
    candidates_text = ""
    for i, cand in enumerate(candidates, 1):
        candidates_text += f"""
Candidate {i}: {cand.candidate_name}
  Match Score: {cand.match_score:.1f}%
  Matched Skills: {', '.join(cand.matched_skills)}
  Strengths: {', '.join(cand.strengths)}
  Improvement Areas: {', '.join(cand.improvement_areas)}
  Overall Assessment: {cand.overall_assessment}
"""
    
    # Format requirements
    must_haves = [f"{r.name}" for r in jd_requirements.must_have_requirements[:5]]
    nice_to_haves = [f"{r.name}" for r in jd_requirements.nice_to_have_requirements[:3]]
    
    requirements_text = f"""
Must-Have: {', '.join(must_haves)}
Nice-to-Have: {', '.join(nice_to_haves)}
"""
    
    # Determine prompt based on comparison type
    if comparison_type == "detailed":
        analysis_prompt = """
Provide a DETAILED comparison analysis covering:
1. Skill alignment for each candidate
2. Experience level assessment
3. Gaps vs. must-haves
4. Strengths in context of role
5. Recommendation ranking (1st choice, 2nd, etc.)
6. Risk factors for each candidate
"""
    else:  # brief
        analysis_prompt = """
Provide a BRIEF comparison summary:
1. Quick ranking (1st, 2nd, 3rd choice)
2. Key differentiators between top candidates
3. Single sentence recommendation for each
"""
    
    prompt = f"""
Compare these candidates for the {jd_requirements.title} role at {jd_requirements.company}.

JOB REQUIREMENTS:
{requirements_text}

CANDIDATES:
{candidates_text}

{analysis_prompt}

Format your response as structured JSON:
{{
    "ranking": [
        {{"position": 1, "candidate_name": "name", "reason": "why they rank 1st"}},
        {{"position": 2, "candidate_name": "name", "reason": "why they rank 2nd"}},
        ...
    ],
    "key_differentiators": "What separates the top candidates?",
    "recommendation": "Overall hiring recommendation",
    "risks": ["risk 1", "risk 2"],
    "detailed_analysis": {{"candidate_name": "analysis text", ...}}
}}
"""
    
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    response_text = message.content[0].text
    
    # Extract JSON
    try:
        # Try direct JSON parse
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON in response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # Return text if JSON parsing fails
            result = {
                "ranking": [],
                "key_differentiators": response_text,
                "recommendation": "See analysis below",
                "detailed_analysis": {"raw_response": response_text}
            }
    
    return result


def get_comparison_summary(comparison: dict) -> str:
    """
    Format comparison results as human-readable text.
    
    Args:
        comparison: Result from compare_candidates()
    
    Returns:
        Formatted string
    """
    
    summary = "\n=== CANDIDATE COMPARISON ===\n\n"
    
    # Ranking
    if comparison.get("ranking"):
        summary += "RANKING:\n"
        for item in comparison["ranking"]:
            summary += f"  {item['position']}. {item['candidate_name']}: {item['reason']}\n"
    
    # Key differentiators
    if comparison.get("key_differentiators"):
        summary += f"\nKEY DIFFERENTIATORS:\n{comparison['key_differentiators']}\n"
    
    # Recommendation
    if comparison.get("recommendation"):
        summary += f"\nRECOMMENDATION:\n{comparison['recommendation']}\n"
    
    # Risks
    if comparison.get("risks"):
        summary += "\nRISKS:\n"
        for risk in comparison["risks"]:
            summary += f"  • {risk}\n"
    
    return summary


def head_to_head_comparison(
    candidate_1: CandidateMatch,
    candidate_2: CandidateMatch,
    jd_requirements: ExtractedJD
) -> str:
    """
    Generate a head-to-head comparison between two specific candidates.
    
    Args:
        candidate_1: First candidate
        candidate_2: Second candidate
        jd_requirements: Job requirements context
    
    Returns:
        Formatted comparison text
    """
    
    comparison = compare_candidates(
        [candidate_1, candidate_2],
        jd_requirements,
        comparison_type="detailed"
    )
    
    return get_comparison_summary(comparison)


if __name__ == "__main__":
    # Test with sample data
    sample_jd = ExtractedJD(
        jd_text="Sample JD",
        title="Senior Backend Engineer",
        company="TechCorp",
        location="Remote",
        must_have_requirements=[],
        nice_to_have_requirements=[],
        summary="Build scalable backend systems"
    )
    
    cand_1 = CandidateMatch(
        candidate_name="John Doe",
        resume_path="resumes/john.pdf",
        match_score=76.7,
        matched_skills=["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        gap_analysis={"kubernetes": "missing"},
        strengths=["Strong Python", "Microservices experience"],
        improvement_areas=["Kubernetes", "GraphQL"],
        overall_assessment="Good match for role"
    )
    
    cand_2 = CandidateMatch(
        candidate_name="Alice Johnson",
        resume_path="resumes/alice.pdf",
        match_score=74.9,
        matched_skills=["Python", "FastAPI", "PostgreSQL", "AWS", "Kubernetes"],
        gap_analysis={"redis": "not mentioned"},
        strengths=["Kubernetes expert", "7 years experience"],
        improvement_areas=["Redis", "Caching strategies"],
        overall_assessment="Strong candidate, slightly less Python depth"
    )
    
    print("Testing Candidate Comparison...\n")
    result = compare_candidates([cand_1, cand_2], sample_jd, "brief")
    print(json.dumps(result, indent=2))
