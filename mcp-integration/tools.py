import os
import json
from typing import List, Dict

def list_resumes(directory: str) -> List[str]:
    """List all resume files"""
    return sorted([f for f in os.listdir(directory) if f.endswith('.json')])

def parse_resume(filepath: str) -> Dict:
    """Read a resume file"""
    with open(filepath) as f:
        return json.load(f)

def extract_skills(resume: Dict) -> List[str]:
    """Get skills from resume"""
    return resume.get('skills', [])

def score_matches(resume: Dict, job_description: str) -> float:
    """Score how well resume matches job"""
    skills = extract_skills(resume)
    job_lower = job_description.lower()
    matches = sum(1 for s in skills if s.lower() in job_lower)
    return round(matches / len(skills), 2) if skills else 0.0

def rank_candidates(resumes: List[Dict], job_description: str) -> List[Dict]:
    """Rank resumes by score"""
    ranked = []
    for r in resumes:
        ranked.append({
            'id': r.get('id'),
            'name': r.get('name'),
            'score': score_matches(r, job_description)
        })
    return sorted(ranked, key=lambda x: x['score'], reverse=True)