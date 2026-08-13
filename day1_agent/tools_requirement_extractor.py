"""
Requirement Extraction Tool
Uses Claude API to intelligently parse job descriptions and extract:
- Must-have requirements
- Nice-to-have requirements
- Skills, experience, education, certifications
"""

import json
import re
from typing import Optional
from anthropic import Anthropic
from state_schema import ExtractedJD, Requirement


# Initialize Anthropic client (uses ANTHROPIC_API_KEY from .env)
client = Anthropic()


def extract_requirements(jd_text: str) -> ExtractedJD:
    """
    Parse a job description and extract structured requirements using Claude API.
    
    Args:
        jd_text: Raw job description text
    
    Returns:
        ExtractedJD with parsed must-have and nice-to-have requirements
    """
    
    # Claude prompt to structure requirements extraction
    prompt = f"""
Analyze this job description and extract requirements in JSON format.

JOB DESCRIPTION:
{jd_text}

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:
{{
    "title": "Job title",
    "company": "Company name if mentioned, else 'Not specified'",
    "location": "Location if mentioned, else 'Not specified'",
    "summary": "2-3 sentence summary of the role",
    "must_have": [
        {{
            "name": "requirement name",
            "category": "skill|experience|education|certification|other",
            "description": "brief description",
            "years_required": 3  (only if relevant, else null)
        }}
    ],
    "nice_to_have": [
        {{
            "name": "requirement name",
            "category": "skill|experience|education|certification|other",
            "description": "brief description",
            "years_required": null
        }}
    ]
}}

Guidelines:
- "must_have": Required to apply (explicitly stated as "required", "must have", "essential")
- "nice_to_have": Preferred but not required ("preferred", "nice to have", "desired")
- For experience years: extract only if explicitly stated (e.g., "5+ years")
- Categories: skill (technical/soft), experience (domain/role), education (degree), certification, other
- Include specific tech stacks, frameworks, tools as skills
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
    
    # Extract JSON from response
    response_text = message.content[0].text
    
    # Try to parse JSON (Claude should return valid JSON)
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse Claude response as JSON: {response_text}")
    
    # Convert to ExtractedJD
    must_have = [
        Requirement(
            name=req["name"],
            category=req["category"],
            is_must_have=True,
            description=req.get("description"),
            years_required=req.get("years_required")
        )
        for req in data.get("must_have", [])
    ]
    
    nice_to_have = [
        Requirement(
            name=req["name"],
            category=req["category"],
            is_must_have=False,
            description=req.get("description"),
            years_required=req.get("years_required")
        )
        for req in data.get("nice_to_have", [])
    ]
    
    extracted = ExtractedJD(
        jd_text=jd_text,
        title=data.get("title", "Unknown"),
        company=data.get("company", "Not specified"),
        location=data.get("location", "Not specified"),
        must_have_requirements=must_have,
        nice_to_have_requirements=nice_to_have,
        summary=data.get("summary", "")
    )
    
    return extracted


def summarize_requirements(extracted_jd: ExtractedJD) -> str:
    """
    Generate a human-readable summary of extracted requirements.
    
    Args:
        extracted_jd: Parsed job description
    
    Returns:
        Formatted string summary
    """
    
    summary = f"""
JOB: {extracted_jd.title} at {extracted_jd.company}
LOCATION: {extracted_jd.location}

SUMMARY: {extracted_jd.summary}

MUST-HAVE REQUIREMENTS ({len(extracted_jd.must_have_requirements)}):
"""
    
    for req in extracted_jd.must_have_requirements:
        years_str = f" ({req.years_required}+ years)" if req.years_required else ""
        summary += f"  • {req.name}{years_str} [{req.category}]\n"
    
    summary += f"\nNICE-TO-HAVE REQUIREMENTS ({len(extracted_jd.nice_to_have_requirements)}):\n"
    
    for req in extracted_jd.nice_to_have_requirements:
        summary += f"  • {req.name} [{req.category}]\n"
    
    return summary


if __name__ == "__main__":
    # Test with a sample JD
    sample_jd = """
    Senior Backend Engineer - Python FastAPI
    
    Company: TechCorp
    Location: Remote
    
    About the Role:
    We are hiring a Senior Backend Engineer to build scalable microservices for our platform.
    
    Required Skills:
    - 5+ years of backend development experience
    - Expert-level Python skills
    - Strong experience with FastAPI framework
    - PostgreSQL and Redis expertise
    - Docker and Kubernetes knowledge
    - AWS cloud platform experience
    - REST API design and implementation
    - Microservices architecture understanding
    
    Nice to Have:
    - Experience with GraphQL
    - Knowledge of message queues (RabbitMQ, Kafka)
    - CI/CD pipeline setup
    - Experience with gRPC
    """
    
    print("Testing Requirement Extraction...\n")
    result = extract_requirements(sample_jd)
    print(summarize_requirements(result))
