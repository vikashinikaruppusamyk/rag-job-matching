"""
Multi-Round Screening Pipeline
3-stage candidate filtering and evaluation.
Round 1: Initial screening (top 10 from all)
Round 2: Deep analysis (top 5 from 10)
Round 3: Final evaluation (top 1-3 candidates)
"""

import json
from typing import Optional
from anthropic import Anthropic

from state_schema import CandidateMatch, ExtractedJD
from tools_candidate_ranker import CandidateRanker
from tools_interview_generator import generate_interview_questions, format_interview_guide

client = Anthropic()


class MultiRoundScreening:
    """
    Multi-stage candidate screening pipeline.
    """
    
    def __init__(self):
        self.ranker = CandidateRanker()
        self.current_round = 1
        self.results = {}
    
    def round_1_screening(self, candidates: list[CandidateMatch], jd: ExtractedJD, 
                         top_n: int = 10) -> dict:
        """
        ROUND 1: Initial Screening
        - Select top 10 candidates from all
        - Focus on basic qualification match
        - Fast evaluation
        
        Args:
            candidates: All candidates
            jd: Job description
            top_n: Number to advance to round 2
        
        Returns:
            Results dict with advanced candidates
        """
        print("\n" + "="*60)
        print("ROUND 1: INITIAL SCREENING")
        print("="*60)
        print(f"Evaluating {len(candidates)} candidates...")
        
        # Rank all candidates
        ranked = self.ranker.rank_candidates(candidates, jd, use_claude=False)
        
        # Get top N
        shortlisted = ranked[:top_n]
        
        # Create assessment
        assessment = self._create_round_assessment(
            round_num=1,
            candidates=shortlisted,
            jd=jd,
            focus="Basic qualification match"
        )
        
        self.results['round_1'] = {
            'candidates': shortlisted,
            'assessment': assessment,
            'advanced_count': len(shortlisted),
            'eliminated': len(candidates) - len(shortlisted)
        }
        
        print(f"\n✅ ROUND 1 COMPLETE")
        print(f"   Advanced: {len(shortlisted)} candidates")
        print(f"   Eliminated: {len(candidates) - len(shortlisted)} candidates")
        
        return self.results['round_1']
    
    def round_2_screening(self, candidates: list[CandidateMatch], jd: ExtractedJD,
                         top_n: int = 5) -> dict:
        """
        ROUND 2: Deep Analysis
        - Deep dive into top 5 candidates
        - Assess technical depth and culture fit
        - Use Claude for intelligent analysis
        - Generate interview questions
        
        Args:
            candidates: Top candidates from round 1
            jd: Job description
            top_n: Number to advance to round 3
        
        Returns:
            Results dict with deeply analyzed candidates
        """
        print("\n" + "="*60)
        print("ROUND 2: DEEP ANALYSIS")
        print("="*60)
        print(f"Deep analyzing {len(candidates)} candidates...")
        
        # Use Claude for intelligent ranking
        ranked = self.ranker.rank_candidates(candidates, jd, use_claude=True)
        
        # Get top N
        finalists = ranked[:top_n]
        
        # Generate interview questions for each
        for candidate in finalists:
            print(f"\n📋 Generating questions for {candidate.candidate_name}...")
            try:
                questions = generate_interview_questions(
                    candidate, jd, interview_round=1, num_questions=3
                )
                candidate.overall_assessment = f"Score: {candidate.match_score:.1f}%. " + \
                                             f"{len(questions.get('questions', []))} screening questions ready."
            except Exception as e:
                print(f"   ⚠️  Could not generate questions: {e}")
        
        # Create assessment
        assessment = self._create_round_assessment(
            round_num=2,
            candidates=finalists,
            jd=jd,
            focus="Technical depth and culture fit"
        )
        
        self.results['round_2'] = {
            'candidates': finalists,
            'assessment': assessment,
            'advanced_count': len(finalists),
            'eliminated': len(candidates) - len(finalists)
        }
        
        print(f"\n✅ ROUND 2 COMPLETE")
        print(f"   Advanced: {len(finalists)} candidates")
        print(f"   Eliminated: {len(candidates) - len(finalists)} candidates")
        
        return self.results['round_2']
    
    def round_3_screening(self, candidates: list[CandidateMatch], jd: ExtractedJD) -> dict:
        """
        ROUND 3: Final Evaluation
        - Final recommendation
        - Hire/No-Hire decisions
        - Risk assessment
        - Onboarding plan
        
        Args:
            candidates: Top candidates from round 2
            jd: Job description
        
        Returns:
            Final recommendation results
        """
        print("\n" + "="*60)
        print("ROUND 3: FINAL EVALUATION")
        print("="*60)
        print(f"Final evaluation of {len(candidates)} candidates...")
        
        # Use Claude for final recommendation
        final_ranking = self.ranker.rank_candidates(candidates, jd, use_claude=True)
        
        # Generate technical round interview for top candidate
        if final_ranking:
            top = final_ranking[0]
            print(f"\n🎯 Top recommendation: {top.candidate_name}")
            
            try:
                tech_questions = generate_interview_questions(
                    top, jd, interview_round=2, num_questions=5
                )
                print(f"   Generated {len(tech_questions.get('questions', []))} technical questions")
            except Exception as e:
                print(f"   ⚠️  Could not generate technical questions: {e}")
        
        # Get final recommendation from Claude
        final_rec = self._get_final_recommendation(final_ranking, jd)
        
        self.results['round_3'] = {
            'candidates': final_ranking,
            'assessment': final_rec,
            'top_recommendation': final_ranking[0] if final_ranking else None,
            'hire_recommendation': final_rec.get('recommendation', 'No recommendation')
        }
        
        print(f"\n✅ ROUND 3 COMPLETE - FINAL DECISION")
        print(f"   Top candidate: {final_ranking[0].candidate_name if final_ranking else 'None'}")
        print(f"   Recommendation: {final_rec.get('recommendation', 'No recommendation')}")
        
        return self.results['round_3']
    
    def _create_round_assessment(self, round_num: int, candidates: list[CandidateMatch],
                                jd: ExtractedJD, focus: str) -> str:
        """
        Create assessment for a round.
        """
        assessment = f"""
ROUND {round_num} ASSESSMENT
Focus: {focus}

Top Candidates:
"""
        for i, cand in enumerate(candidates[:3], 1):
            assessment += f"\n{i}. {cand.candidate_name} ({cand.match_score:.1f}%)"
            assessment += f"\n   Skills: {', '.join(cand.matched_skills[:5])}"
            assessment += f"\n   Assessment: {cand.overall_assessment}"
        
        return assessment
    
    def _get_final_recommendation(self, candidates: list[CandidateMatch], 
                                 jd: ExtractedJD) -> dict:
        """
        Get final hire/no-hire recommendation from Claude.
        """
        if not candidates:
            return {'recommendation': 'No candidates qualified', 'reasoning': ''}
        
        top = candidates[0]
        
        prompt = f"""
Make a final HIRE/NO-HIRE recommendation for this role.

ROLE: {jd.title} at {jd.company}
TOP CANDIDATE: {top.candidate_name}
Score: {top.match_score:.1f}%

Skills: {', '.join(top.matched_skills[:10])}
Gaps: {', '.join(top.gap_analysis.get('missing_must_have', [])[:3]) or 'None'}

Return ONLY JSON:
{{
    "recommendation": "HIRE" or "NO-HIRE" or "CONDITIONAL",
    "reasoning": "Why hire or not hire",
    "confidence": 0.0-1.0,
    "onboarding_focus": "What to focus on during onboarding",
    "risks": ["risk1", "risk2"],
    "next_steps": ["step1", "step2"]
}}
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"⚠️  Error getting recommendation: {e}")
            return {
                'recommendation': 'CONDITIONAL',
                'reasoning': f'Score: {top.match_score:.1f}%',
                'confidence': top.match_score / 100,
                'onboarding_focus': 'Technical skills and systems',
                'risks': list(top.gap_analysis.get('missing_must_have', [])[:2]),
                'next_steps': ['Schedule technical interview', 'Prepare assessment']
            }
    
    def run_full_pipeline(self, candidates: list[CandidateMatch], 
                         jd: ExtractedJD) -> dict:
        """
        Run the complete 3-round screening pipeline.
        
        Args:
            candidates: All candidates
            jd: Job description
        
        Returns:
            Complete pipeline results
        """
        print("\n" + "="*70)
        print(" "*15 + "MULTI-ROUND SCREENING PIPELINE")
        print("="*70)
        
        # Round 1
        r1 = self.round_1_screening(candidates, jd, top_n=10)
        
        # Round 2
        r2 = self.round_2_screening(r1['candidates'], jd, top_n=5)
        
        # Round 3
        r3 = self.round_3_screening(r2['candidates'], jd)
        
        # Summary
        summary = self._create_pipeline_summary()
        
        return {
            'round_1': r1,
            'round_2': r2,
            'round_3': r3,
            'summary': summary,
            'top_recommendation': r3['top_recommendation']
        }
    
    def _create_pipeline_summary(self) -> str:
        """
        Create summary of entire pipeline.
        """
        r1 = self.results.get('round_1', {})
        r2 = self.results.get('round_2', {})
        r3 = self.results.get('round_3', {})
        
        summary = f"""
SCREENING PIPELINE SUMMARY
═════════════════════════════

ROUND 1 (Initial Screen):
  Candidates: {len(r1.get('candidates', []))} selected
  Eliminated: {r1.get('eliminated', 0)}

ROUND 2 (Deep Analysis):
  Candidates: {len(r2.get('candidates', []))} selected
  Eliminated: {r2.get('eliminated', 0)}

ROUND 3 (Final Decision):
  Top Recommendation: {r3.get('top_recommendation').candidate_name if r3.get('top_recommendation') else 'None'}
  Recommendation: {r3.get('hire_recommendation', 'Pending')}

NEXT STEPS:
  1. Schedule interviews with selected candidates
  2. Prepare technical assessments
  3. Plan onboarding program
"""
        return summary


def run_screening_pipeline(candidates: list[CandidateMatch], 
                          jd: ExtractedJD) -> dict:
    """
    Convenience function to run complete screening pipeline.
    """
    pipeline = MultiRoundScreening()
    return pipeline.run_full_pipeline(candidates, jd)


if __name__ == "__main__":
    print("Multi-round screening pipeline test")
