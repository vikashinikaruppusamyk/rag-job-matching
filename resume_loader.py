import os
import pdfplumber
from pathlib import Path

def load_resume(file_path: str) -> str:
    """Load resume text from PDF or TXT."""
    if file_path.endswith('.pdf'):
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''.join(page.extract_text() or '' for page in pdf.pages)
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    else:
        print(f"Unsupported file format: {file_path}")
        return ""

def list_resumes(resume_dir: str = './data/resumes') -> list:
    """List all resume files in directory."""
    if not os.path.exists(resume_dir):
        print(f"Directory not found: {resume_dir}")
        return []
    
    resume_files = [
        f for f in os.listdir(resume_dir)
        if f.endswith(('.pdf', '.txt', '.docx'))
    ]
    
    return resume_files

if __name__ == '__main__':
    # Test: List resumes
    resumes = list_resumes()
    print(f"Found {len(resumes)} resumes")
    
    # Test: Load first resume (if any)
    if resumes:
        first_resume = resumes[0]
        path = f'./data/resumes/{first_resume}'
        text = load_resume(path)
        print(f"\nLoaded: {first_resume}")
        print(f"Text length: {len(text)} characters")
        print(f"First 200 chars: {text[:200]}")