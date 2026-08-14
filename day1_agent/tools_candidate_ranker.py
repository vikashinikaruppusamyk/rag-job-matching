"""
Candidate Ranker Tool
Uses hybrid scoring + Claude API for intelligent candidate ranking.
Combines: semantic similarity, keyword matching, and AI reasoning.
"""

import json
import re
from typing import Optional
from anthropic import Anthropic

from state_schema import CandidateMatch, ExtractedJD

client = Anthropic()


class CandidateRanker:
    """
    Intelligently rank candidates using hybrid scoring.
    """
    
    def __init__(self):
        self.ranker_model = "claude-opus-4-6"
    
    def calculate_gap_analysis(self, candidate: CandidateMatch, jd: ExtractedJD) -> dict:
        """
        Analyze skills gaps between candidate and job requirements.
        
        Args:
            candidate: The candidate
            jd: Job requirements
        
        Returns:
            Dictionary with gaps and strengths
        """
        candidate_skills = set([s.lower() for s in candidate.matched_skills])
        must_have = set([r.name.lower() for r in jd.must_have_requirements])
        nice_have = set([r.name.lower() for r in jd.nice_to_have_requirements])
        
        # Calculate gaps
        missing_must_have = must_have - candidate_skills
        missing_nice_have = nice_have - candidate_skills
        
        # Calculate strengths (skills beyond requirements)
        extra_skills = candidate_skills - (must_have | nice_have)
        
        return {
            'missing_must_have': list(missing_must_have),
            'missing_nice_have': list(missing_nice_have),
            'extra_skills': list(extra_skills),
            'must_have_coverage': len(must_have - missing_must_have) / len(must_have) if must_have else 0,
            'nice_have_coverage': len(nice_have - missing_nice_have) / len(nice_have) if nice_have else 0,
        }
    
    def rank_candidates(self, candidates: list[CandidateMatch], jd: ExtractedJD, 
                       use_claude: bool = True) -> list[CandidateMatch]:
        """
        Rank candidates by fit using hybrid scoring.
        
        Args:
            candidates: List of candidates to rank
            jd: Job requirements
            use_claude: Use Claude for intelligent ranking (True) or just scoring (False)
        
        Returns:
            Ranked list of candidates with updated assessments
        """
        
        if not candidates:
            return []
        
        print(f"\n🎯 Ranking {len(candidates)} candidates for {jd.title}...")
        
        # Analyze each candidate
        for candidate in candidates:
            gap_analysis = self.calculate_gap_analysis(candidate, jd)
            candidate.gap_analysis = gap_analysis
        
        # Use Claude for intelligent ranking if available
        if use_claude:
            candidates = self._rank_with_claude(candidates, jd)
        else:
            candidates = self._rank_by_scoring(candidates)
        
        # Sort by match score
        candidates.sort(key=lambda x: x.match_score, reverse=True)
        
        # Print rankings
        print("\n📊 RANKINGS:")
        for i, cand in enumerate(candidates[:5], 1):
            print(f"  {i}. {cand.candidate_name}: {cand.match_score:.1f}%")
            print(f"     {cand.overall_assessment[:80]}...")
        
        return candidates
    
    def _rank_by_scoring(self, candidates: list[CandidateMatch]) -> list[CandidateMatch]:
        """
        Simple scoring-based ranking without Claude.
        """
        for candidate in candidates:
            gaps = candidate.gap_analysis
            
            # Score based on coverage percentages
            must_have_score = gaps.get('must_have_coverage', 0) * 100
            nice_have_score = gaps.get('nice_have_coverage', 0) * 50
            
            # Hybrid score (initial semantic + keyword from searcher)
            final_score = (candidate.match_score * 0.7) + (must_have_score * 0.3)
            candidate.match_score = final_score
            
            # Update assessment
            missing = gaps.get('missing_must_have', [])
            if missing:
                candidate.overall_assessment = f"Score: {final_score:.1f}%. Missing: {', '.join(missing[:2])}"
            else:
                candidate.overall_assessment = f"Score: {final_score:.1f}%. Covers all must-haves."
        
        return candidates
    
    def _rank_with_claude(self, candidates: list[CandidateMatch], jd: ExtractedJD) -> list[CandidateMatch]:
        """
        Use Claude API for intelligent ranking with reasoning.
        """
        
        # Format candidates for Claude
        candidates_text = ""
        for i, cand in enumerate(candidates, 1):
            gaps = cand.gap_analysis
            candidates_text += f"""
Candidate {i}: {cand.candidate_name}
  Current Score: {cand.match_score:.1f}%
  Skills: {', '.join(cand.matched_skills[:8])}
  Must-Have Coverage: {gaps.get('must_have_coverage', 0)*100:.0f}%
  Missing Must-Haves: {', '.join(gaps.get('missing_must_have', [])[:3]) or 'None'}
  Missing Nice-to-Haves: {', '.join(gaps.get('missing_nice_have', [])[:3]) or 'None'}
"""
        
        # Format requirements
        must_haves = [r.name for r in jd.must_have_requirements[:5]]
        nice_haves = [r.name for r in jd.nice_to_have_requirements[:3]]
        
        prompt = f"""
Rank these candidates for the {jd.title} role at {jd.company}.

KEY REQUIREMENTS:
Must-Have: {', '.join(must_haves)}
Nice-to-Have: {', '.join(nice_haves)}

CANDIDATES:
{candidates_text}

Provide a ranking with intelligent reasoning. Return ONLY valid JSON:
{{
    "ranking": [
        {{"position": 1, "candidate_name": "name", "final_score": 85, "reasoning": "Why they rank 1st"}},
        {{"position": 2, "candidate_name": "name", "final_score": 78, "reasoning": "Why they rank 2nd"}},
        ...
    ],
    "top_recommendation": "name of best candidate",
    "key_differentiators": "What separates top candidates?"
}}

Scoring guidelines:
- 85-100: Perfect fit or excellent match (most must-haves + nice-to-haves)
- 70-84: Good fit (all must-haves, few nice-to-haves)
- 55-69: Moderate fit (most must-haves, gaps in some)
- 40-54: Weak fit (missing key must-haves)
- <40: Poor fit (significant gaps)
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parse response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse Claude response")
            
            # Update candidates with Claude's scores and reasoning
            ranking = result.get("ranking", [])
            for rank_item in ranking:
                cand_name = rank_item.get("candidate_name")
                score = rank_item.get("final_score", 0)
                reasoning = rank_item.get("reasoning", "")
                
                # Find and update candidate
                for cand in candidates:
                    if cand.candidate_name == cand_name:
                        cand.match_score = score
                        cand.overall_assessment = reasoning
                        
                        # Parse gaps for strengths/improvements
                        gaps = cand.gap_analysis
                        if gaps.get('missing_must_have'):
                            cand.improvement_areas = gaps['missing_must_have']
                        
                        # Strengths are covered must-haves
                        covered = len([r for r in jd.must_have_requirements 
                                     if r.name.lower() not in [s.lower() for s in gaps.get('missing_must_have', [])]])
                        if covered > 0:
                            cand.strengths = [f"Covers {covered}/{len(jd.must_have_requirements)} must-haves"]
                        
                        break
            
            return candidates
            
        except Exception as e:
            print(f"⚠️ Claude ranking failed, using basic scoring: {e}")
            return self._rank_by_scoring(candidates)
    
    def get_top_n(self, candidates: list[CandidateMatch], n: int = 5) -> list[CandidateMatch]:
        """
        Get top N candidates.
        """
        return sorted(candidates, key=lambda x: x.match_score, reverse=True)[:n]
    
    def generate_shortlist(self, candidates: list[CandidateMatch], 
                          threshold: float = 70.0) -> list[CandidateMatch]:
        """
        Generate shortlist of candidates above threshold.
        
        Args:
            candidates: All candidates
            threshold: Minimum score to include (0-100)
        
        Returns:
            Candidates above threshold
        """
        shortlist = [c for c in candidates if c.match_score >= threshold]
        shortlist.sort(key=lambda x: x.match_score, reverse=True)
        return shortlist


def rank_candidates(candidates: list[CandidateMatch], jd: ExtractedJD) -> list[CandidateMatch]:
    """
    Convenience function to rank candidates.
    """
    ranker = CandidateRanker()
    return ranker.rank_candidates(candidates, jd, use_claude=True)


if __name__ == "__main__":
    # Test
    from state_schema import Requirement
    
    sample_jd = ExtractedJD(
        jd_text="Sample",
        title="Senior Backend Engineer",
        company="TechCorp",
        location="Remote",
        must_have_requirements=[
            Requirement(name="Python", category="skill", is_must_have=True),
            Requirement(name="FastAPI", category="skill", is_must_have=True),
            Requirement(name="PostgreSQL", category="skill", is_must_have=True),
        ],
        nice_to_have_requirements=[
            Requirement(name="GraphQL", category="skill", is_must_have=False),
        ],
        summary="Build scalable microservices"
    )
    
    sample_candidates = [
        CandidateMatch(
            candidate_name="John Doe",
            resume_path="resumes/john.pdf",
            match_score=76.7,
            matched_skills=["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
            gap_analysis={},
            strengths=["Expert Python"],
            improvement_areas=["GraphQL"],
            overall_assessment="Strong match"
        ),
        CandidateMatch(
            candidate_name="Alice Johnson",
            resume_path="resumes/alice.pdf",
            match_score=74.9,
            matched_skills=["Python", "Django", "PostgreSQL"],
            gap_analysis={},
            strengths=["7 years experience"],
            improvement_areas=["FastAPI", "GraphQL"],
            overall_assessment="Good match"
        ),
    ]
    
    print("Testing Candidate Ranker...\n")
    ranked = rank_candidates(sample_candidates, sample_jd)
    print(f"\nTop candidate: {ranked[0].candidate_name} ({ranked[0].match_score:.1f}%)")
