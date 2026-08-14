"""
Report Generator
Creates professional hiring reports with candidate assessments.
"""

import json
from datetime import datetime
from anthropic import Anthropic

from state_schema import CandidateMatch, ExtractedJD

client = Anthropic()


class ReportGenerator:
    """
    Generate professional hiring reports.
    """
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_match_report(self, candidates: list[CandidateMatch], 
                             jd: ExtractedJD) -> str:
        """
        Generate detailed hiring match report.
        
        Args:
            candidates: Ranked candidates
            jd: Job description
        
        Returns:
            Professional report text
        """
        
        if not candidates:
            return "No candidates to report on."
        
        print("\n📄 Generating match report...")
        
        # Use Claude to write professional report
        candidates_json = json.dumps([
            {
                'name': c.candidate_name,
                'score': c.match_score,
                'skills': c.matched_skills[:8],
                'gaps': c.gap_analysis.get('missing_must_have', [])[:3],
                'assessment': c.overall_assessment
            }
            for c in candidates[:5]
        ], indent=2)
        
        prompt = f"""
Generate a professional hiring report for this position.

POSITION: {jd.title} at {jd.company}
LOCATION: {jd.location}
SUMMARY: {jd.summary}

TOP CANDIDATES:
{candidates_json}

Requirements:
Must-Have: {', '.join([r.name for r in jd.must_have_requirements[:5]])}
Nice-to-Have: {', '.join([r.name for r in jd.nice_to_have_requirements[:3]])}

Create a professional report including:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. TOP RECOMMENDATION (who to hire first)
3. CANDIDATE PROFILES (for top 3)
   - Strengths
   - Gaps
   - Fit score
4. RISK ASSESSMENT
5. RECOMMENDED NEXT STEPS

Format as clean, readable prose suitable for hiring decision makers.
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            report = message.content[0].text
            return report
            
        except Exception as e:
            print(f"⚠️  Error generating report: {e}")
            return self._generate_simple_report(candidates, jd)
    
    def generate_candidate_profile(self, candidate: CandidateMatch, 
                                  jd: ExtractedJD) -> str:
        """
        Generate detailed profile for a single candidate.
        
        Args:
            candidate: The candidate
            jd: Job description
        
        Returns:
            Candidate profile text
        """
        
        print(f"\n👤 Generating profile for {candidate.candidate_name}...")
        
        gaps = candidate.gap_analysis
        
        prompt = f"""
Generate a detailed candidate profile for hiring consideration.

CANDIDATE: {candidate.candidate_name}
MATCH SCORE: {candidate.match_score:.1f}%
SKILLS: {', '.join(candidate.matched_skills)}

ASSESSMENT VS JOB:
- Must-Have Coverage: {gaps.get('must_have_coverage', 0)*100:.0f}%
- Missing Must-Haves: {', '.join(gaps.get('missing_must_have', [])[:3]) or 'None'}
- Missing Nice-to-Haves: {', '.join(gaps.get('missing_nice_have', [])[:3]) or 'None'}

Create a professional profile including:
1. EXECUTIVE SUMMARY
2. STRENGTHS (why hire this candidate)
3. GAPS & DEVELOPMENT AREAS
4. RAMP-UP TIMELINE (how long to productivity)
5. COMPENSATION RANGE (estimated)
6. INTERVIEW FOCUS AREAS
7. RECOMMENDATION (STRONG HIRE / HIRE / CONSIDER / PASS)

Be honest and specific.
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            profile = message.content[0].text
            return profile
            
        except Exception as e:
            print(f"⚠️  Error generating profile: {e}")
            return self._generate_simple_profile(candidate)
    
    def generate_comparison_report(self, candidates: list[CandidateMatch], 
                                  jd: ExtractedJD) -> str:
        """
        Generate side-by-side comparison report.
        
        Args:
            candidates: Candidates to compare (usually top 3)
            jd: Job description
        
        Returns:
            Comparison report
        """
        
        print(f"\n🔄 Generating comparison report for {len(candidates)} candidates...")
        
        candidates_text = ""
        for i, cand in enumerate(candidates, 1):
            candidates_text += f"""
{i}. {cand.candidate_name} - {cand.match_score:.1f}%
   Skills: {', '.join(cand.matched_skills[:5])}
   Gaps: {', '.join(cand.gap_analysis.get('missing_must_have', [])[:2]) or 'None'}
"""
        
        prompt = f"""
Create a concise side-by-side comparison for hiring decision.

POSITION: {jd.title}
MUST-HAVE SKILLS: {', '.join([r.name for r in jd.must_have_requirements[:5]])}

CANDIDATES:
{candidates_text}

Provide:
1. QUICK COMPARISON TABLE
2. WHO RANKS 1ST AND WHY
3. WHO RANKS 2ND AND WHY
4. KEY DIFFERENTIATORS
5. FINAL RECOMMENDATION

Be concise and decision-focused.
"""
        
        try:
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            report = message.content[0].text
            return report
            
        except Exception as e:
            print(f"⚠️  Error generating comparison: {e}")
            return "Comparison report generation failed"
    
    def generate_summary_statistics(self, candidates: list[CandidateMatch]) -> dict:
        """
        Generate statistics about candidate pool.
        
        Args:
            candidates: All candidates evaluated
        
        Returns:
            Statistics dictionary
        """
        
        if not candidates:
            return {}
        
        scores = [c.match_score for c in candidates]
        
        stats = {
            'total_candidates': len(candidates),
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'median_score': sorted(scores)[len(scores)//2],
            'top_5_avg': sum(sorted(scores, reverse=True)[:5]) / min(5, len(scores)),
        }
        
        return stats
    
    def _generate_simple_report(self, candidates: list[CandidateMatch], 
                               jd: ExtractedJD) -> str:
        """
        Fallback report when Claude unavailable.
        """
        report = f"""
HIRING REPORT
═════════════════════

Position: {jd.title} at {jd.company}
Generated: {self.timestamp}

TOP CANDIDATES:
"""
        for i, cand in enumerate(candidates[:5], 1):
            report += f"""
{i}. {cand.candidate_name} - {cand.match_score:.1f}%
   Skills: {', '.join(cand.matched_skills[:5])}
   Assessment: {cand.overall_assessment}
"""
        
        report += f"""

RECOMMENDATION:
Proceed with interview process for top 3 candidates.
Start with {candidates[0].candidate_name}.

NEXT STEPS:
1. Schedule screening interviews
2. Prepare technical assessments
3. Plan reference checks
"""
        return report
    
    def _generate_simple_profile(self, candidate: CandidateMatch) -> str:
        """
        Fallback profile generation.
        """
        gaps = candidate.gap_analysis
        
        profile = f"""
CANDIDATE PROFILE
═════════════════

Name: {candidate.candidate_name}
Match Score: {candidate.match_score:.1f}%

SKILLS:
{', '.join(candidate.matched_skills)}

STRENGTHS:
{chr(10).join(['- ' + s for s in candidate.strengths]) if candidate.strengths else 'Strong skill match'}

GAPS:
{chr(10).join(['- ' + g for g in gaps.get('missing_must_have', [])[:3]]) if gaps.get('missing_must_have') else 'Covers all must-haves'}

RECOMMENDATION:
{"STRONG HIRE" if candidate.match_score >= 80 else "HIRE" if candidate.match_score >= 70 else "CONSIDER" if candidate.match_score >= 60 else "PASS"}
"""
        return profile
    
    def save_report(self, report_text: str, filename: str) -> None:
        """
        Save report to file.
        
        Args:
            report_text: Report content
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"✅ Report saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")


def generate_report(candidates: list[CandidateMatch], jd: ExtractedJD) -> str:
    """
    Convenience function to generate report.
    """
    generator = ReportGenerator()
    return generator.generate_match_report(candidates, jd)


if __name__ == "__main__":
    print("Report generator test")
