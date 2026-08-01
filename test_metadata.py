from smart_chunking import extract_metadata
from resume_loader import load_resume

# Test with our sample resume
text = load_resume('./data/resumes/sample_resume.txt')
metadata = extract_metadata(text, 'sample_resume.txt')

print("=" * 60)
print("METADATA EXTRACTION TEST")
print("=" * 60)
print(f"Name: {metadata['name']}")
print(f"Years of Experience: {metadata['years_exp']}")
print(f"Skills ({len(metadata['skills'])} detected):")
for skill in sorted(metadata['skills']):
    print(f"  - {skill}")
print("=" * 60)