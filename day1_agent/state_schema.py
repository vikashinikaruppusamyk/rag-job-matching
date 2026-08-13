"""
State schema for the matching agent.
Defines the shape of data flowing through the LangGraph agent.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Requirement(BaseModel):
    """A single requirement (must-have or nice-to-have)."""
    name: str
    category: str  # e.g., "skill", "experience", "education"
    is_must_have: bool
    description: Optional[str] = None
    years_required: Optional[int] = None


class ExtractedJD(BaseModel):
    """Parsed job description with extracted requirements."""
    jd_text: str
    title: str
    company: str
    location: str
    must_have_requirements: list[Requirement]
    nice_to_have_requirements: list[Requirement]
    summary: str


class CandidateMatch(BaseModel):
    """A single candidate with their match details."""
    candidate_name: str
    resume_path: str
    match_score: float
    matched_skills: list[str]
    gap_analysis: dict[str, Any]  # skills/exp gaps
    strengths: list[str]
    improvement_areas: list[str]
    overall_assessment: str


class ConversationMessage(BaseModel):
    """A single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class MatchingAgentState(BaseModel):
    """
    Complete state of the matching agent.
    Used by LangGraph to track agent memory across steps.
    """
    # Conversation
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    
    # Job Description & Requirements
    current_jd_text: Optional[str] = None
    extracted_jd: Optional[ExtractedJD] = None
    requirement_filters: dict[str, Any] = Field(default_factory=dict)  # user adjustments
    
    # Candidate Shortlist
    all_candidates: list[CandidateMatch] = Field(default_factory=list)
    shortlisted_candidates: list[CandidateMatch] = Field(default_factory=list)
    final_recommendation: Optional[str] = None
    
    # Agent Flow Control
    current_step: str = "START"  # tracks position in workflow
    error_message: Optional[str] = None
    reasoning_trace: list[str] = Field(default_factory=list)  # log of agent decisions
    
    # Multi-round screening
    screening_round: int = 1  # 1, 2, or 3
    round_1_top_n: int = 10  # from 100
    round_2_top_n: int = 5   # from 10
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class ToolInput(BaseModel):
    """Base class for tool inputs."""
    pass


class ExtractRequirementsInput(ToolInput):
    """Input for requirement extraction tool."""
    jd_text: str


class SearchResumesInput(ToolInput):
    """Input for resume search tool."""
    requirements: ExtractedJD
    top_k: int = 10


class ComparedCandidatesInput(ToolInput):
    """Input for candidate comparison tool."""
    candidate_ids: list[str]  # candidate names or indices
    comparison_type: str = "brief"  # "brief" or "detailed"


class GenerateInterviewQuestionsInput(ToolInput):
    """Input for interview question generator."""
    candidate_name: str
    candidate_match: CandidateMatch
    interview_round: int = 1  # 1st, 2nd, 3rd round screening
