import re
from typing import List, Tuple, Dict

def detect_sections(text: str) -> List[Tuple[str, int, int]]:
    """
    Detect resume sections (Education, Experience, Skills, etc.)
    Returns list of (section_name, start_pos, end_pos)
    """
    section_patterns = {
        'contact': r'(?:email|phone|linkedin|github|website)',
        'summary': r'(?:professional summary|executive summary|about|objective)',
        'experience': r'(?:work experience|professional experience|employment|jobs|career|experience)',
        'education': r'(?:education|academic|degree|university|college)',
        'skills': r'(?:technical skills|skills|competencies|expertise|technologies)',
        'projects': r'(?:projects|portfolio|side projects|open source)',
        'certifications': r'(?:certifications|licenses|awards|publications)',
    }
    
    sections = []
    text_lower = text.lower()
    
    # Find all section headers
    for section_name, pattern in section_patterns.items():
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            start = match.start()
            sections.append((section_name, start))
    
    # Sort by position
    sections.sort(key=lambda x: x[1])
    
    # Add end positions (next section starts where this one ends)
    result = []
    for i, (name, start) in enumerate(sections):
        if i < len(sections) - 1:
            end = sections[i + 1][1]
        else:
            end = len(text)
        result.append((name, start, end))
    
    return result

def chunk_text(text: str, max_chunk_size: int = 500) -> List[Tuple[str, str]]:
    """
    Chunk text by sections, preserving context.
    Returns list of (section_name, chunk_text).
    """
    sections = detect_sections(text)
    chunks = []
    
    # If no sections detected, fallback to paragraph chunking
    if not sections:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        for para in paragraphs:
            if para:
                chunks.append(('body', para))
        return chunks
    
    # Process each section
    for section_name, start, end in sections:
        section_text = text[start:end].strip()
        
        if not section_text:
            continue
        
        # If section is too long, split into sub-chunks
        if len(section_text.split()) > max_chunk_size:
            sub_chunks = section_text.split('\n\n')
            current = ''
            
            for sub_chunk in sub_chunks:
                if len((current + ' ' + sub_chunk).split()) <= max_chunk_size:
                    current += ' ' + sub_chunk
                else:
                    if current.strip():
                        chunks.append((section_name, current.strip()))
                    current = sub_chunk
            
            if current.strip():
                chunks.append((section_name, current.strip()))
        else:
            chunks.append((section_name, section_text))
    
    return chunks

def extract_metadata(text: str, file_path: str) -> Dict:
    """Extract name, years of experience, skills."""
    
    # Extract name (usually first line with capitalized words)
    lines = text.split('\n')
    name = None
    for line in lines[:5]:
        if len(line.split()) <= 4 and any(w[0].isupper() for w in line.split()):
            name = line.strip()
            break
    
    if not name:
        name = file_path.split('/')[-1].replace('.pdf', '').replace('.docx', '').replace('.txt', '')
    
    # Extract years of experience
    years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs)', text.lower())
    years_exp = int(years_match.group(1)) if years_match else 0
    
    # Extract skills (common tech keywords)
    skills_keywords = [
        'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'php', 'ruby',
        'react', 'angular', 'vue', 'fastapi', 'django', 'flask', 'spring', 'node', 'express',
        'sql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform',
        'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
        'rest api', 'graphql', 'microservices', 'devops'
    ]
    
    skills = []
    text_lower = text.lower()
    for skill in skills_keywords:
        if re.search(r'\b' + skill + r'\b', text_lower):
            skills.append(skill.title())
    
    return {
        'name': name,
        'years_exp': years_exp,
        'skills': list(set(skills))  # Remove duplicates
    }

# ===== TEST =====

if __name__ == '__main__':
    sample_resume = """
    John Doe
    john@example.com | linkedin.com/in/johndoe
    
    PROFESSIONAL SUMMARY
    Backend engineer with 5 years of experience building scalable APIs.
    
    WORK EXPERIENCE
    Senior Backend Engineer at TechCorp (2022-Present)
    - Built REST APIs using FastAPI and Python
    - Managed PostgreSQL databases
    - 5+ years experience with backend systems
    
    Backend Developer at StartupXYZ (2019-2022)
    - Developed Django applications
    
    EDUCATION
    B.Tech in Computer Science
    University of XYZ, 2019
    
    SKILLS
    Languages: Python, JavaScript, Go
    Frameworks: FastAPI, Django, React
    Databases: PostgreSQL, MongoDB
    Cloud: AWS, Docker, Kubernetes
    """
    
    # Test section detection
    print("=" * 60)
    print("SECTION DETECTION TEST")
    print("=" * 60)
    sections = detect_sections(sample_resume)
    print(f"Detected {len(sections)} sections:")
    for name, start, end in sections:
        print(f"  - {name.upper()}: {end - start} chars")
    
    # Test chunking
    print("\n" + "=" * 60)
    print("CHUNKING TEST")
    print("=" * 60)
    chunks = chunk_text(sample_resume)
    print(f"Created {len(chunks)} chunks:")
    for i, (section, text) in enumerate(chunks):
        words = len(text.split())
        print(f"  Chunk {i+1} ({section}): {words} words")
    
    # Test metadata extraction
    print("\n" + "=" * 60)
    print("METADATA EXTRACTION TEST")
    print("=" * 60)
    metadata = extract_metadata(sample_resume, 'john_doe.pdf')
    print(f"Name: {metadata['name']}")
    print(f"Years: {metadata['years_exp']}")
    print(f"Skills: {metadata['skills']}")