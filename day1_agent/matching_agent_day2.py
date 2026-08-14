"""
Updated Matching Agent - DAY 2
Integrates: ChromaDB search, hybrid ranking, multi-round screening, reporting
"""

import os
import json
from typing import Any
from dotenv import load_dotenv

from state_schema import (
    MatchingAgentState,
    ConversationMessage,
    ExtractedJD,
)
from tools_requirement_extractor import extract_requirements, summarize_requirements
from tools_resume_search import search_resumes
from tools_candidate_ranker import rank_candidates
from tools_multi_round_screening import run_screening_pipeline
from tools_report_generator import ReportGenerator
from tools_compare_candidates import compare_candidates, get_comparison_summary
from tools_interview_generator import generate_interview_questions, format_interview_guide

load_dotenv()


class MatchingAgent:
    """
    Updated Matching Agent with Day 2 enhancements.
    - Resume search from ChromaDB
    - Hybrid candidate ranking
    - Multi-round screening pipeline
    - Professional reporting
    """
    
    def __init__(self):
        self.state = MatchingAgentState()
        self.conversation_context = ""
        self.report_generator = ReportGenerator()
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        msg = ConversationMessage(role=role, content=content)
        self.state.conversation_history.append(msg)
        self.conversation_context += f"\n{role.upper()}: {content}"
    
    def log_reasoning(self, step: str, reasoning: str):
        """Log agent reasoning for explainability."""
        self.state.reasoning_trace.append(f"[{step}] {reasoning}")
        print(f"  📝 {step}: {reasoning}")
    
    # ============= STEP 1: PARSE JD =============
    def parse_jd(self, jd_text: str) -> ExtractedJD:
        """Step 1: Parse job description using Claude."""
        print("\n[Step 1] Parsing Job Description...")
        self.state.current_step = "PARSE_JD"
        self.state.current_jd_text = jd_text
        
        try:
            extracted = extract_requirements(jd_text)
            self.state.extracted_jd = extracted
            
            self.log_reasoning(
                "PARSE_JD",
                f"Parsed JD: {extracted.title} at {extracted.company}"
            )
            
            return extracted
        except Exception as e:
            self.state.error_message = f"Error parsing JD: {str(e)}"
            self.log_reasoning("PARSE_JD_ERROR", str(e))
            raise
    
    # ============= STEP 2: EXTRACT REQUIREMENTS =============
    def extract_jd_requirements(self) -> ExtractedJD:
        """Step 2: Extract structured requirements."""
        print("\n[Step 2] Extracting Requirements...")
        self.state.current_step = "EXTRACT_REQUIREMENTS"
        
        if not self.state.extracted_jd:
            raise ValueError("JD not parsed yet. Call parse_jd() first.")
        
        jd = self.state.extracted_jd
        
        summary = summarize_requirements(jd)
        self.log_reasoning(
            "REQUIREMENTS_EXTRACTED", 
            f"{len(jd.must_have_requirements)} must-haves, {len(jd.nice_to_have_requirements)} nice-to-haves"
        )
        
        print(summary)
        return jd
    
    # ============= STEP 3: SEARCH RESUMES =============
    def search_resumes(self, top_k: int = 10) -> list:
        """Step 3: Search ChromaDB for matching resumes (DAY 2 NEW)."""
        print(f"\n[Step 3] Searching Resumes (top {top_k})...")
        self.state.current_step = "SEARCH_RESUMES"
        
        if not self.state.extracted_jd:
            raise ValueError("JD not parsed yet.")
        
        jd = self.state.extracted_jd
        
        try:
            # Use hybrid search from tools_resume_search
            candidates = search_resumes(jd, top_k=top_k)
            
            self.state.all_candidates = candidates
            self.log_reasoning(
                "RESUME_SEARCH",
                f"Found {len(candidates)} candidates matching requirements"
            )
            
            print(f"\n✅ Found {len(candidates)} candidates")
            for i, cand in enumerate(candidates[:5], 1):
                print(f"   {i}. {cand.candidate_name} ({cand.match_score:.1f}%)")
            
            return candidates
            
        except Exception as e:
            self.state.error_message = f"Error searching resumes: {str(e)}"
            self.log_reasoning("SEARCH_ERROR", str(e))
            print(f"⚠️  {str(e)}")
            return []
    
    # ============= STEP 4: RANK CANDIDATES =============
    def rank_candidates(self) -> list:
        """Step 4: Rank candidates using hybrid scoring (DAY 2 ENHANCED)."""
        print("\n[Step 4] Ranking Candidates with Intelligence...")
        self.state.current_step = "RANK_CANDIDATES"
        
        if not self.state.all_candidates:
            print("No candidates to rank.")
            return []
        
        if not self.state.extracted_jd:
            raise ValueError("JD not parsed yet.")
        
        jd = self.state.extracted_jd
        candidates = self.state.all_candidates
        
        try:
            # Use Claude-powered ranking
            ranked = rank_candidates(candidates, jd)
            
            # Shortlist top 5
            self.state.shortlisted_candidates = ranked[:5]
            
            self.log_reasoning(
                "RANKING_COMPLETE",
                f"Ranked {len(ranked)} candidates, shortlisted {len(self.state.shortlisted_candidates)}"
            )
            
            return self.state.shortlisted_candidates
            
        except Exception as e:
            self.state.error_message = f"Error ranking: {str(e)}"
            self.log_reasoning("RANKING_ERROR", str(e))
            print(f"⚠️  {str(e)}")
            return []
    
    # ============= STEP 5: MULTI-ROUND SCREENING =============
    def run_screening_pipeline(self) -> dict:
        """Step 5: Run multi-round screening (DAY 2 NEW)."""
        print("\n[Step 5] Running Multi-Round Screening Pipeline...")
        self.state.current_step = "MULTI_ROUND_SCREENING"
        
        if not self.state.extracted_jd or not self.state.all_candidates:
            return {'status': 'error', 'message': 'Missing JD or candidates'}
        
        try:
            jd = self.state.extracted_jd
            candidates = self.state.all_candidates
            
            # Run 3-round screening
            pipeline_results = run_screening_pipeline(candidates, jd)
            
            self.log_reasoning(
                "SCREENING_COMPLETE",
                f"Pipeline complete. Top recommendation: {pipeline_results['top_recommendation'].candidate_name}"
            )
            
            return pipeline_results
            
        except Exception as e:
            self.state.error_message = f"Error in screening: {str(e)}"
            self.log_reasoning("SCREENING_ERROR", str(e))
            return {'status': 'error', 'message': str(e)}
    
    # ============= STEP 6: GENERATE REPORTS =============
    def generate_match_report(self) -> str:
        """Step 6: Generate professional matching report (DAY 2 ENHANCED)."""
        print("\n[Step 6] Generating Professional Report...")
        self.state.current_step = "GENERATE_REPORT"
        
        if not self.state.shortlisted_candidates:
            return "No candidates to report on."
        
        try:
            jd = self.state.extracted_jd
            candidates = self.state.shortlisted_candidates
            
            # Generate detailed report
            report = self.report_generator.generate_match_report(candidates, jd)
            
            self.state.final_recommendation = report
            self.log_reasoning("REPORT_GENERATED", "Match report created")
            
            return report
            
        except Exception as e:
            self.state.error_message = f"Error generating report: {str(e)}"
            self.log_reasoning("REPORT_ERROR", str(e))
            return f"Report generation failed: {str(e)}"
    
    # ============= MAIN WORKFLOW =============
    def run_matching_workflow(self, jd_text: str, use_screening_pipeline: bool = True) -> dict:
        """
        Execute the complete matching workflow (DAY 2 ENHANCED).
        
        Args:
            jd_text: The job description text
            use_screening_pipeline: Use multi-round screening (True) or simple ranking (False)
        
        Returns:
            Dictionary with results and state
        """
        print("\n" + "="*60)
        print("STARTING MATCHING WORKFLOW (DAY 2)")
        print("="*60)
        
        try:
            # Step 1: Parse JD
            self.parse_jd(jd_text)
            
            # Step 2: Extract Requirements
            self.extract_jd_requirements()
            
            # Step 3: Search Resumes (DAY 2 NEW)
            candidates = self.search_resumes(top_k=10)
            
            if not candidates:
                print("⚠️  No candidates found")
                return {
                    "status": "no_candidates",
                    "jd_title": self.state.extracted_jd.title,
                    "candidates_found": 0
                }
            
            # Step 4: Rank Candidates (DAY 2 ENHANCED)
            ranked = self.rank_candidates()
            
            # Step 5: Multi-Round Screening (DAY 2 NEW)
            if use_screening_pipeline:
                screening_results = self.run_screening_pipeline()
            else:
                screening_results = None
            
            # Step 6: Generate Report (DAY 2 ENHANCED)
            report = self.generate_match_report()
            
            print("\n" + "="*60)
            print("WORKFLOW COMPLETE")
            print("="*60)
            
            return {
                "status": "success",
                "jd_title": self.state.extracted_jd.title,
                "candidates_found": len(self.state.all_candidates),
                "shortlisted": len(self.state.shortlisted_candidates),
                "report": report,
                "screening_results": screening_results,
                "reasoning_trace": self.state.reasoning_trace
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "reasoning_trace": self.state.reasoning_trace
            }


# ============= TEST / MAIN =============
if __name__ == "__main__":
    # Sample JD
    sample_jd = """
    Senior Backend Engineer - Python FastAPI
    
    Company: TechCorp
    Location: Remote
    
    We are hiring a Senior Backend Engineer to build scalable microservices.
    
    Requirements:
    - 5+ years of backend development experience
    - Expert-level Python skills
    - Strong experience with FastAPI framework
    - PostgreSQL and Redis expertise
    - Docker and Kubernetes knowledge
    - AWS cloud platform experience
    
    Nice to Have:
    - Experience with GraphQL
    - Knowledge of message queues (RabbitMQ, Kafka)
    - CI/CD pipeline setup
    """
    
    # Run agent
    agent = MatchingAgent()
    result = agent.run_matching_workflow(sample_jd, use_screening_pipeline=True)
    
    print("\n" + "="*60)
    print("FINAL REPORT:")
    print("="*60)
    print(result["report"])
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY:")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Candidates Found: {result.get('candidates_found', 0)}")
    print(f"Shortlisted: {result.get('shortlisted', 0)}")
