import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from resume_loader import load_resume, list_resumes
from smart_chunking import chunk_text, extract_metadata

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def embed_text(text: str) -> list:
    """Convert text to embedding using OpenAI."""
    try:
        response = client.embeddings.create(
            model='text-embedding-3-small',
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error creating embedding: {e}")
        return None

def process_resume_embeddings(file_path: str, resume_number: int, total: int) -> dict:
    """Load resume → chunk → embed → return data."""
    print(f"  [{resume_number}/{total}] {os.path.basename(file_path)}...", end=' ', flush=True)
    
    try:
        # Load and chunk
        text = load_resume(file_path)
        if not text:
            print("✗ (empty)")
            return {}
        
        chunks = chunk_text(text)
        metadata = extract_metadata(text, file_path)
        
        embeddings_data = {}
        
        # Embed each chunk
        for i, (section, chunk_text_content) in enumerate(chunks):
            embedding = embed_text(chunk_text_content)
            
            if embedding is None:
                print("✗ (embedding failed)")
                return {}
            
            doc_id = f"{metadata['name']}_chunk_{i}"
            embeddings_data[doc_id] = {
                'embedding': embedding,
                'text': chunk_text_content,
                'section': section,
                'metadata': metadata
            }
            
            # Rate limiting: 1 request per 0.5 seconds
            time.sleep(0.5)
        
        print(f"✓ ({len(chunks)} chunks)")
        return embeddings_data
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return {}

def generate_all_embeddings(resume_dir: str = './data/resumes', output_file: str = 'embeddings_cache.json'):
    """Process all resumes and save embeddings."""
    
    resumes = list_resumes(resume_dir)
    
    if not resumes:
        print(f"No resumes found in {resume_dir}")
        print("Please add some .pdf or .txt files to that directory.")
        return
    
    print(f"\nProcessing {len(resumes)} resumes for embeddings...\n")
    
    all_embeddings = {}
    success_count = 0
    
    for i, resume_file in enumerate(resumes, 1):
        file_path = os.path.join(resume_dir, resume_file)
        embeddings = process_resume_embeddings(file_path, i, len(resumes))
        
        if embeddings:
            all_embeddings.update(embeddings)
            success_count += 1
    
    # Save to file
    if all_embeddings:
        with open(output_file, 'w') as f:
            json.dump(all_embeddings, f, indent=2)
        
        total_chunks = len(all_embeddings)
        print(f"\n✓ Successfully processed {success_count}/{len(resumes)} resumes")
        print(f"✓ Generated {total_chunks} embeddings")
        print(f"✓ Saved to {output_file}")
    else:
        print(f"\n✗ No embeddings generated. Check your resumes.")

if __name__ == '__main__':
    generate_all_embeddings()