"""
Interview Question Generator Tool
Uses Claude API to generate intelligent, role-specific interview questions.
"""

import json
import re
from anthropic import Anthropic
from state_schema import CandidateMatch, ExtractedJD


client = Anthropic()


def generate_interview_questions(
    candidate: CandidateMatch,
    jd_requirements: ExtractedJD,
    interview_round: int = 1,
    num_questions: int = 5
) -> dict:
    """
    Generate interview questions tailored to a candidate and role.
    
    Args:
        candidate: The candidate being interviewed
        jd_requirements: Job requirements context
        interview_round: 1 (screening), 2 (technical), 3 (final)
        num_questions: Number of questions to generate
    
    Returns:
        Dictionary with questions and guidance
    """
    
    # Determine interview focus based on round
    if interview_round == 1:
        focus = """
SCREENING ROUND (Phone/Initial):
- Culture fit and motivation
- Experience validation
- Problem-solving approach
- Why they're interested in the role
"""
    elif interview_round == 2:
        focus = """
TECHNICAL ROUND:
- Deep technical skills in their gaps
- Project experience
- Architecture decisions
- Handling challenges
"""
    else:  # round 3
        focus = """
FINAL ROUND:
- Leadership/teamwork
- Long-term goals alignment
- Company culture fit
- Decision-making scenarios
"""
    
    # Format candidate info
    strengths = ", ".join(candidate.strengths) if candidate.strengths else "Not specified"
    gaps = ", ".join(candidate.improvement_areas) if candidate.improvement_areas else "None"
    skills = ", ".join(candidate.matched_skills) if candidate.matched_skills else "Not specified"
    
    # Format requirements
    must_haves = [r.name for r in jd_requirements.must_have_requirements[:3]]
    must_haves_text = ", ".join(must_haves) if must_haves else "Not specified"
    
    prompt = f"""
Generate {num_questions} interview questions for:

CANDIDATE: {candidate.candidate_name}
Match Score: {candidate.match_score:.1f}%
Skills: {skills}
Strengths: {strengths}
Improvement Areas: {gaps}

ROLE: {jd_requirements.title}
COMPANY: {jd_requirements.company}
KEY REQUIREMENTS: {must_haves_text}

{focus}

Return ONLY valid JSON (no markdown):
{{
    "interview_round": {interview_round},
    "candidate_name": "{candidate.candidate_name}",
    "role": "{jd_requirements.title}",
    "focus_areas": ["area1", "area2", ...],
    "questions": [
        {{
            "question_number": 1,
            "question": "The actual question?",
            "category": "technical|behavioral|motivation|culture",
            "why_this_question": "Why ask this specific candidate this question?",
            "what_to_listen_for": "Key indicators of good answer"
        }},
        ...
    ],
    "red_flags": ["flag1", "flag2"],
    "follow_up_topics": ["topic1", "topic2"]
}}

Guidelines:
- Questions should be tailored to the candidate's profile
- Address gaps in skills/experience
- Validate strengths
- Be specific (reference their background if possible)
- Avoid generic questions
"""
    
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    response_text = message.content[0].text
    
    # Parse JSON response
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "interview_round": interview_round,
                "candidate_name": candidate.candidate_name,
                "role": jd_requirements.title,
                "questions": [],
                "error": "Could not parse response",
                "raw_response": response_text
            }
    
    return result


def format_interview_guide(questions_data: dict) -> str:
    """
    Format interview questions as a readable guide for the interviewer.
    
    Args:
        questions_data: Result from generate_interview_questions()
    
    Returns:
        Formatted interview guide text
    """
    
    guide = f"""
=== INTERVIEW GUIDE ===

CANDIDATE: {questions_data.get('candidate_name', 'Unknown')}
ROLE: {questions_data.get('role', 'Unknown')}
ROUND: {questions_data.get('interview_round', 1)} ("""
    
    round_names = {1: "Screening", 2: "Technical", 3: "Final"}
    guide += f"{round_names.get(questions_data.get('interview_round', 1), 'Unknown')})\n\n"
    
    # Focus areas
    focus_areas = questions_data.get('focus_areas', [])
    if focus_areas:
        guide += "FOCUS AREAS:\n"
        for area in focus_areas:
            guide += f"  • {area}\n"
        guide += "\n"
    
    # Questions
    questions = questions_data.get('questions', [])
    if questions:
        guide += f"INTERVIEW QUESTIONS ({len(questions)}):\n"
        for q in questions:
            guide += f"""
{q.get('question_number', 0)}. {q.get('question', 'Question not found')}
   Category: {q.get('category', 'general')}
   Why: {q.get('why_this_question', 'Context not provided')}
   Listen for: {q.get('what_to_listen_for', 'Key points')}
"""
    
    # Red flags
    red_flags = questions_data.get('red_flags', [])
    if red_flags:
        guide += "\nRED FLAGS TO WATCH FOR:\n"
        for flag in red_flags:
            guide += f"  ⚠️  {flag}\n"
    
    # Follow-up topics
    follow_ups = questions_data.get('follow_up_topics', [])
    if follow_ups:
        guide += "\nFOLLOW-UP TOPICS IF TIME PERMITS:\n"
        for topic in follow_ups:
            guide += f"  • {topic}\n"
    
    return guide


def generate_all_rounds(
    candidate: CandidateMatch,
    jd_requirements: ExtractedJD
) -> dict:
    """
    Generate interview questions for all 3 rounds.
    
    Args:
        candidate: The candidate
        jd_requirements: Job requirements
    
    Returns:
        Dictionary with all 3 rounds of questions
    """
    
    all_rounds = {}
    for round_num in [1, 2, 3]:
        all_rounds[f"round_{round_num}"] = generate_interview_questions(
            candidate,
            jd_requirements,
            interview_round=round_num,
            num_questions=5
        )
    
    return all_rounds


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
    
    sample_candidate = CandidateMatch(
        candidate_name="John Doe",
        resume_path="resumes/john.pdf",
        match_score=76.7,
        matched_skills=["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        gap_analysis={"kubernetes": "missing", "redis": "limited"},
        strengths=["Strong Python", "Microservices experience", "AWS expertise"],
        improvement_areas=["Kubernetes", "GraphQL", "caching strategies"],
        overall_assessment="Good match for role"
    )
    
    print("Testing Interview Question Generation (Round 1)...\n")
    questions = generate_interview_questions(sample_candidate, sample_jd, interview_round=1)
    print(format_interview_guide(questions))
