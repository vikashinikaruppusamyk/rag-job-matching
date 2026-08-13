"""
Matching Agent using LangGraph
Orchestrates the candidate matching workflow:
START → Parse JD → Extract Requirements → Search Resumes → Rank → Report → Feedback Loop → END
"""

import os
import json
from typing import Any
from dotenv import load_dotenv
from anthropic import Anthropic
import chromadb

from state_schema import (
    MatchingAgentState,
    ConversationMessage,
    CandidateMatch,
    ExtractedJD,
    Requirement
)
from tools_requirement_extractor import extract_requirements, summarize_requirements
from tools_compare_candidates import compare_candidates, get_comparison_summary
from tools_interview_generator import generate_interview_questions, format_interview_guide

load_dotenv()

# Initialize clients
anthropic_client = Anthropic()
chroma_client = chromadb.PersistentClient(path="./chroma_data")


class MatchingAgent:
    """
    LangGraph-based matching agent.
    Manages conversation state and orchestrates matching workflow.
    """
    
    def __init__(self):
        self.state = MatchingAgentState()
        self.conversation_context = ""
    
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
        """
        Step 1: Parse job description using Claude.
        Extract title, company, location, summary.
        """
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
        """
        Step 2: Extract structured requirements (must-have vs nice-to-have).
        Already done in parse_jd, but this is the explicit step.
        """
        print("\n[Step 2] Extracting Requirements...")
        self.state.current_step = "EXTRACT_REQUIREMENTS"
        
        if not self.state.extracted_jd:
            raise ValueError("JD not parsed yet. Call parse_jd() first.")
        
        jd = self.state.extracted_jd
        
        # Apply any user filters
        if self.state.requirement_filters:
            self.log_reasoning(
                "APPLY_FILTERS",
                f"Applied user filters: {self.state.requirement_filters}"
            )
        
        summary = summarize_requirements(jd)
        self.log_reasoning("REQUIREMENTS_EXTRACTED", f"{len(jd.must_have_requirements)} must-haves, {len(jd.nice_to_have_requirements)} nice-to-haves")
        
        print(summary)
        return jd
    
    # ============= STEP 3: SEARCH RESUMES =============
    def search_resumes(self, top_k: int = 10) -> list[CandidateMatch]:
        """
        Step 3: Search ChromaDB for matching resumes.
        Use existing hybrid_matcher.py or ChromaDB API directly.
        """
        print(f"\n[Step 3] Searching Resumes (top {top_k})...")
        self.state.current_step = "SEARCH_RESUMES"
        
        if not self.state.extracted_jd:
            raise ValueError("JD not parsed yet.")
        
        jd = self.state.extracted_jd
        
        try:
            # Query ChromaDB collection
            collection = chroma_client.get_collection(name="resumes")
            
            # Create search query from must-have requirements
            search_query = " ".join([
                req.name for req in jd.must_have_requirements[:5]
            ])
            
            # Embed query using OpenAI (same model as resumes)
            # Note: In production, we'd use the vector_db.py embed_query function
            from openai import OpenAI
            openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            query_embedding = openai_client.embeddings.create(
                model='text-embedding-3-small',
                input=search_query
            ).data[0].embedding
            
            # Query ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Convert results to CandidateMatch objects
            candidates = []
            for doc_id, distance, metadata, document in zip(
                results['ids'][0],
                results['distances'][0],
                results['metadatas'][0],
                results['documents'][0]
            ):
                # Convert distance to similarity (0-100)
                match_score = max(0, (1 - distance) * 100)
                
                candidate = CandidateMatch(
                    candidate_name=metadata.get('name', 'Unknown'),
                    resume_path=metadata.get('resume_path', ''),
                    match_score=match_score,
                    matched_skills=metadata.get('skills', '').split(','),
                    gap_analysis={},
                    strengths=[],
                    improvement_areas=[],
                    overall_assessment=f"Semantic similarity: {match_score:.1f}%"
                )
                candidates.append(candidate)
            
            self.state.all_candidates = candidates
            self.log_reasoning(
                "RESUME_SEARCH",
                f"Found {len(candidates)} candidates matching requirements"
            )
            
            return candidates
            
        except Exception as e:
            self.state.error_message = f"Error searching resumes: {str(e)}"
            self.log_reasoning("SEARCH_ERROR", str(e))
            # Return empty list if search fails
            return []
    
    # ============= STEP 4: RANK CANDIDATES =============
    def rank_candidates(self) -> list[CandidateMatch]:
        """
        Step 4: Rank candidates using Claude API for intelligent scoring.
        """
        print("\n[Step 4] Ranking Candidates with Intelligence...")
        self.state.current_step = "RANK_CANDIDATES"
        
        if not self.state.all_candidates:
            print("No candidates to rank.")
            return []
        
        if not self.state.extracted_jd:
            raise ValueError("JD not parsed yet.")
        
        jd = self.state.extracted_jd
        candidates = self.state.all_candidates[:10]  # Rank top 10
        
        # Use Claude to intelligently rank
        candidates_text = "\n".join([
            f"{i}. {c.candidate_name} (Score: {c.match_score:.1f}%, Skills: {', '.join(c.matched_skills[:5])})"
            for i, c in enumerate(candidates, 1)
        ])
        
        prompt = f"""
Rank these candidates for the {jd.title} role at {jd.company}.

MUST-HAVE REQUIREMENTS:
{', '.join([r.name for r in jd.must_have_requirements[:5]])}

CANDIDATES:
{candidates_text}

Return ONLY JSON with ranking and analysis:
{{
    "ranking": [
        {{"position": 1, "candidate_name": "name", "reasoning": "why"}},
        ...
    ],
    "shortlist": ["top 3-5 candidates"]
}}
"""
        
        message = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response = json.loads(message.content[0].text)
        
        # Reorder candidates based on ranking
        ranking = response.get("ranking", [])
        shortlist = response.get("shortlist", [])
        
        # Sort candidates by ranking
        ranked_candidates = []
        for rank_item in ranking:
            for candidate in candidates:
                if candidate.candidate_name == rank_item.get("candidate_name"):
                    ranked_candidates.append(candidate)
                    break
        
        self.state.shortlisted_candidates = ranked_candidates[:5]
        
        self.log_reasoning(
            "RANKING_COMPLETE",
            f"Shortlisted {len(self.state.shortlisted_candidates)} candidates"
        )
        
        return self.state.shortlisted_candidates
    
    # ============= STEP 5: GENERATE REPORT =============
    def generate_match_report(self) -> str:
        """
        Step 5: Generate detailed match report with analysis.
        """
        print("\n[Step 5] Generating Match Report...")
        self.state.current_step = "GENERATE_REPORT"
        
        if not self.state.shortlisted_candidates:
            return "No candidates to report on."
        
        jd = self.state.extracted_jd
        candidates = self.state.shortlisted_candidates
        
        # Use Claude to generate detailed report
        candidates_json = json.dumps([
            {
                "name": c.candidate_name,
                "score": c.match_score,
                "skills": c.matched_skills,
                "assessment": c.overall_assessment
            }
            for c in candidates
        ])
        
        prompt = f"""
Generate a hiring match report for the {jd.title} position.

JOB: {jd.title} at {jd.company}
SUMMARY: {jd.summary}

TOP CANDIDATES:
{candidates_json}

Include:
1. Executive summary (2-3 sentences)
2. Top recommendation with reasoning
3. Strengths of top 3 candidates
4. Risk factors
5. Next steps (interviews, technical assessments)

Keep it concise and actionable.
"""
        
        message = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        report = message.content[0].text
        self.state.final_recommendation = report
        
        self.log_reasoning("REPORT_GENERATED", "Match report created")
        
        return report
    
    # ============= MAIN WORKFLOW =============
    def run_matching_workflow(self, jd_text: str) -> dict:
        """
        Execute the complete matching workflow.
        
        Args:
            jd_text: The job description text
        
        Returns:
            Dictionary with results and state
        """
        print("\n" + "="*60)
        print("STARTING MATCHING WORKFLOW")
        print("="*60)
        
        try:
            # Step 1: Parse JD
            self.parse_jd(jd_text)
            
            # Step 2: Extract Requirements
            self.extract_jd_requirements()
            
            # Step 3: Search Resumes
            candidates = self.search_resumes(top_k=10)
            
            # Step 4: Rank Candidates
            ranked = self.rank_candidates()
            
            # Step 5: Generate Report
            report = self.generate_match_report()
            
            print("\n" + "="*60)
            print("WORKFLOW COMPLETE")
            print("="*60)
            
            return {
                "status": "success",
                "jd_title": self.state.extracted_jd.title if self.state.extracted_jd else "",
                "candidates_found": len(self.state.all_candidates),
                "shortlisted": len(self.state.shortlisted_candidates),
                "report": report,
                "reasoning_trace": self.state.reasoning_trace
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "reasoning_trace": self.state.reasoning_trace
            }
    
    def handle_user_refinement(self, user_query: str) -> str:
        """
        Handle mid-conversation user refinements (iterative feedback).
        
        Args:
            user_query: User's natural language request
        
        Returns:
            Agent response
        """
        self.add_to_history("user", user_query)
        
        # Use Claude to interpret user intent
        prompt = f"""
User is refining a candidate matching process. Their request:
"{user_query}"

Current context:
- JD: {self.state.extracted_jd.title if self.state.extracted_jd else 'Not set'}
- Shortlisted candidates: {len(self.state.shortlisted_candidates)}
- Candidates found: {len(self.state.all_candidates)}

Interpret their request. Return JSON:
{{
    "intent": "adjust_requirements|compare_candidates|explain_ranking|show_details|other",
    "action": "What specific action to take"
}}
"""
        
        message = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        interpretation = json.loads(message.content[0].text)
        
        # Execute action based on intent
        intent = interpretation.get("intent")
        action = interpretation.get("action")
        
        response = f"Action: {intent} - {action}"
        self.add_to_history("assistant", response)
        
        return response


# ============= TEST / MAIN =============
if __name__ == "__main__":
    # Sample JD for testing
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
    
    # Initialize and run agent
    agent = MatchingAgent()
    result = agent.run_matching_workflow(sample_jd)
    
    print("\n" + "="*60)
    print("FINAL REPORT:")
    print("="*60)
    print(result["report"])
