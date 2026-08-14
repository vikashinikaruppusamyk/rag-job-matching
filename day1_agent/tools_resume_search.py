"""
Resume Search Tool
Queries ChromaDB for candidate resumes matching job requirements.
Supports both semantic search (embeddings) and keyword-based filtering.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

from state_schema import ExtractedJD, CandidateMatch, Requirement

load_dotenv()

# Initialize clients
chroma_client = chromadb.PersistentClient(path="../chroma_data")
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


class ResumeSearcher:
    """
    Search and retrieve candidate resumes from ChromaDB.
    Supports semantic search via embeddings and keyword filtering.
    """
    
    def __init__(self, collection_name: str = "resumes"):
        """
        Initialize resume searcher.
        
        Args:
            collection_name: Name of ChromaDB collection (default: "resumes")
        """
        self.collection_name = collection_name
        try:
            self.collection = chroma_client.get_collection(name=collection_name)
            self.collection_ready = True
            print(f"✅ Connected to ChromaDB collection: {collection_name}")
            print(f"   Total resumes indexed: {self.collection.count()}")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to ChromaDB: {e}")
            self.collection_ready = False
    
    def embed_query(self, query_text: str) -> list[float]:
        """
        Embed query text using OpenAI embeddings (same model as resumes).
        
        Args:
            query_text: Text to embed
        
        Returns:
            Embedding vector
        """
        response = openai_client.embeddings.create(
            model='text-embedding-3-small',
            input=query_text
        )
        return response.data[0].embedding
    
    def semantic_search(self, query_text: str, top_k: int = 10) -> list[dict]:
        """
        Semantic search using embeddings similarity.
        
        Args:
            query_text: Search query
            top_k: Number of results to return
        
        Returns:
            List of candidate results with similarity scores
        """
        if not self.collection_ready:
            print("❌ ChromaDB not available for search")
            return []
        
        try:
            # Embed the query
            query_embedding = self.embed_query(query_text)
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            candidates = []
            for doc_id, distance, metadata, document in zip(
                results['ids'][0],
                results['distances'][0],
                results['metadatas'][0],
                results['documents'][0]
            ):
                # Convert distance to similarity (0-100)
                similarity = max(0, (1 - distance) * 100)
                
                candidate = {
                    'doc_id': doc_id,
                    'name': metadata.get('name', 'Unknown'),
                    'resume_path': metadata.get('resume_path', ''),
                    'years_exp': metadata.get('years_exp', 0),
                    'skills': metadata.get('skills', '').split(',') if metadata.get('skills') else [],
                    'section': metadata.get('section', ''),
                    'semantic_score': similarity,
                    'excerpt': document[:100] + "..." if len(document) > 100 else document
                }
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []
    
    def keyword_search(self, keywords: list[str], top_k: int = 10) -> list[dict]:
        """
        Keyword-based filtering across all resumes.
        Finds resumes containing required keywords.
        
        Args:
            keywords: List of required keywords/skills
            top_k: Maximum results to return
        
        Returns:
            Candidates matching keywords, ranked by match count
        """
        if not self.collection_ready:
            return []
        
        try:
            # Get all candidates
            all_results = self.collection.get()
            
            # Score each candidate by keyword matches
            scored = []
            for doc_id, metadata, document in zip(
                all_results['ids'],
                all_results['metadatas'],
                all_results['documents']
            ):
                # Count keyword matches (case-insensitive)
                doc_text = (document + metadata.get('skills', '')).lower()
                matches = sum(1 for kw in keywords if kw.lower() in doc_text)
                
                if matches > 0:  # Only include if has at least one match
                    keyword_score = (matches / len(keywords)) * 100  # Percentage match
                    
                    scored.append({
                        'doc_id': doc_id,
                        'name': metadata.get('name', 'Unknown'),
                        'resume_path': metadata.get('resume_path', ''),
                        'years_exp': metadata.get('years_exp', 0),
                        'skills': metadata.get('skills', '').split(',') if metadata.get('skills') else [],
                        'keyword_score': keyword_score,
                        'matches': matches,
                        'total_keywords': len(keywords)
                    })
            
            # Sort by keyword score descending
            scored.sort(key=lambda x: x['keyword_score'], reverse=True)
            
            return scored[:top_k]
            
        except Exception as e:
            print(f"❌ Error in keyword search: {e}")
            return []
    
    def hybrid_search(self, jd: ExtractedJD, top_k: int = 10, 
                     semantic_weight: float = 0.6, 
                     keyword_weight: float = 0.4) -> list[CandidateMatch]:
        """
        Hybrid search combining semantic + keyword scoring.
        
        Args:
            jd: Extracted job description
            top_k: Number of results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
        
        Returns:
            List of CandidateMatch objects ranked by hybrid score
        """
        
        if not self.collection_ready:
            print("⚠️  ChromaDB not available. Using mock data for testing.")
            return self._get_mock_candidates(top_k)
        
        # Build search query from requirements
        must_have_keywords = [req.name for req in jd.must_have_requirements]
        nice_have_keywords = [req.name for req in jd.nice_to_have_requirements]
        all_keywords = must_have_keywords + nice_have_keywords
        
        search_query = " ".join(must_have_keywords[:5])  # Top 5 must-haves
        
        # Semantic search
        print(f"🔍 Semantic search: '{search_query}'")
        semantic_results = self.semantic_search(search_query, top_k=20)
        
        # Keyword search
        print(f"🔍 Keyword search: {len(all_keywords)} skills")
        keyword_results = self.keyword_search(all_keywords, top_k=20)
        
        # Merge and score
        merged = {}
        
        # Add semantic results
        for res in semantic_results:
            merged[res['name']] = {
                'semantic_score': res['semantic_score'],
                'keyword_score': 0,
                'data': res
            }
        
        # Add/update with keyword results
        for res in keyword_results:
            if res['name'] in merged:
                merged[res['name']]['keyword_score'] = res['keyword_score']
            else:
                merged[res['name']] = {
                    'semantic_score': 0,
                    'keyword_score': res['keyword_score'],
                    'data': res
                }
        
        # Calculate hybrid scores
        candidates = []
        for name, scores in merged.items():
            hybrid_score = (
                scores['semantic_score'] * semantic_weight +
                scores['keyword_score'] * keyword_weight
            )
            
            data = scores['data']
            candidate = CandidateMatch(
                candidate_name=data.get('name', 'Unknown'),
                resume_path=data.get('resume_path', ''),
                match_score=hybrid_score,
                matched_skills=data.get('skills', [])[:10],  # Top 10 skills
                gap_analysis={},  # Will be filled by ranker
                strengths=[],  # Will be filled by ranker
                improvement_areas=[],  # Will be filled by ranker
                overall_assessment=f"Hybrid score: {hybrid_score:.1f}%"
            )
            candidates.append(candidate)
        
        # Sort by hybrid score
        candidates.sort(key=lambda x: x.match_score, reverse=True)
        
        print(f"✅ Found {len(candidates)} candidates")
        return candidates[:top_k]
    
    def _get_mock_candidates(self, top_k: int = 10) -> list[CandidateMatch]:
        """
        Return mock candidates for testing when ChromaDB unavailable.
        """
        mock = [
            CandidateMatch(
                candidate_name="John Doe",
                resume_path="resumes/john.pdf",
                match_score=76.7,
                matched_skills=["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Kubernetes", "Redis"],
                gap_analysis={"graphql": "missing"},
                strengths=["6 years backend", "Expert Python", "Microservices"],
                improvement_areas=["GraphQL", "Kafka"],
                overall_assessment="Strong match"
            ),
            CandidateMatch(
                candidate_name="Alice Johnson",
                resume_path="resumes/alice.pdf",
                match_score=74.9,
                matched_skills=["Python", "FastAPI", "PostgreSQL", "Kubernetes", "Redis", "Docker"],
                gap_analysis={"aws": "limited"},
                strengths=["7 years experience", "Kubernetes expert"],
                improvement_areas=["AWS", "GraphQL"],
                overall_assessment="Good match"
            ),
            CandidateMatch(
                candidate_name="Frank Chen",
                resume_path="resumes/frank.pdf",
                match_score=63.4,
                matched_skills=["Python", "FastAPI", "AWS", "Docker"],
                gap_analysis={"redis": "missing", "kubernetes": "missing"},
                strengths=["5 years experience", "ML background"],
                improvement_areas=["Redis", "Kubernetes", "FastAPI depth"],
                overall_assessment="Moderate match"
            ),
        ]
        return mock[:top_k]


def search_resumes(jd: ExtractedJD, top_k: int = 10) -> list[CandidateMatch]:
    """
    Convenience function to search resumes for a job description.
    
    Args:
        jd: Extracted job description
        top_k: Number of candidates to return
    
    Returns:
        List of candidate matches
    """
    searcher = ResumeSearcher()
    return searcher.hybrid_search(jd, top_k=top_k)


if __name__ == "__main__":
    # Test
    from state_schema import ExtractedJD, Requirement
    
    sample_jd = ExtractedJD(
        jd_text="Sample JD",
        title="Senior Backend Engineer",
        company="TechCorp",
        location="Remote",
        must_have_requirements=[
            Requirement(name="Python", category="skill", is_must_have=True),
            Requirement(name="FastAPI", category="skill", is_must_have=True),
            Requirement(name="PostgreSQL", category="skill", is_must_have=True),
            Requirement(name="Redis", category="skill", is_must_have=True),
            Requirement(name="Docker", category="skill", is_must_have=True),
        ],
        nice_to_have_requirements=[
            Requirement(name="GraphQL", category="skill", is_must_have=False),
            Requirement(name="Kubernetes", category="skill", is_must_have=False),
        ],
        summary="Build scalable microservices"
    )
    
    print("Testing Resume Search...\n")
    candidates = search_resumes(sample_jd, top_k=5)
    
    print(f"\nFound {len(candidates)} candidates:")
    for i, cand in enumerate(candidates, 1):
        print(f"{i}. {cand.candidate_name} ({cand.match_score:.1f}%)")
        print(f"   Skills: {', '.join(cand.matched_skills[:5])}")
