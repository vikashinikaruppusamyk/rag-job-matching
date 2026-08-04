\# Day 4 Testing Summary (Aug 6, 2026)



\## Database Verification ✓

\- Total embeddings: 333

\- Unique resumes: 30

\- Average chunks per resume: 11

\- Chunk size: 300-500 tokens



\## Smart Chunking Verification ✓

\- Sections detected: Contact, Summary, Experience, Education, Skills, Projects, Certifications

\- All 30 resumes processed successfully

\- Metadata extraction: Name, Years of Experience, Skills



\## Embeddings Verification ✓

\- Model: OpenAI text-embedding-3-small

\- Vector size: 1536 dimensions

\- Encoding format: float32

\- All resumes embedded and cached



\## ChromaDB Storage Verification ✓

\- Storage type: Persistent (./chroma\_data/)

\- Collection: 'resumes'

\- Similarity metric: cosine

\- All embeddings successfully stored



\## Hybrid Search Testing ✓



\### Semantic + Keyword Matching

\- Semantic weight: 70%

\- Keyword weight: 30%

\- Retrieval method: Vector similarity + keyword filtering

\- Must-have filters: Experience level, skills



\### Job Description Test Results



\#### JD 1: Backend Engineer (Python/FastAPI/PostgreSQL)

\- Top match: John Doe (76.7/100)

\- Matched skills: Python, FastAPI, PostgreSQL, Docker, AWS

\- Avg top-3 score: 75.5



\#### JD 2: Machine Learning Engineer (TensorFlow/PyTorch)

\- Top match: Frank Chen (63.2/100)

\- Matched skills: Python, TensorFlow, PyTorch, Deep Learning

\- Avg top-3 score: 59.6

\- Note: Lower scores due to fewer ML specialists in dataset



\#### JD 3: DevOps Engineer (Kubernetes/Docker)

\- Top match: Jack Kumar (68.2/100)

\- Matched skills: Kubernetes, Docker, Terraform, AWS

\- Avg top-3 score: 64.5



\#### JD 4: Full Stack Engineer (React/Node.js)

\- Top match: Henry Brown (67.3/100)

\- Matched skills: JavaScript, React, Node.js, PostgreSQL

\- Avg top-3 score: 67.3



\#### JD 5: Data Engineer (Spark/Hadoop)

\- Top match: Grace Martinez C (68.8/100)

\- Matched skills: Python, Spark

\- Avg top-3 score: 68.7



\## Overall Performance Metrics



| Metric | Value |

|--------|-------|

| Total matches analyzed | 49 |

| Average match score | 57.5/100 |

| Highest score | 76.7/100 |

| Lowest score | 44.9/100 |

| Score distribution spread | 31.8 |

| Average skills matched | 3.8/candidate |

| Max skills matched | 5 |

| Min skills matched | 2 |



\## System Capabilities ✓



1\. \*\*Document Processing\*\*

&#x20;  - Smart chunking by resume sections

&#x20;  - Metadata extraction (name, years, skills)

&#x20;  - Support for multiple file formats (PDF, TXT, DOCX)



2\. \*\*Vector Storage \& Retrieval\*\*

&#x20;  - 333 embeddings indexed in ChromaDB

&#x20;  - Persistent storage on disk

&#x20;  - Fast cosine similarity search (<500ms)



3\. \*\*Hybrid Search \& Matching\*\*

&#x20;  - Semantic similarity (vector-based)

&#x20;  - Keyword matching (exact and fuzzy)

&#x20;  - Combined scoring with adjustable weights

&#x20;  - Must-have requirement filtering



4\. \*\*Output \& Reporting\*\*

&#x20;  - JSON output per specification

&#x20;  - Match scores (0-100)

&#x20;  - Matched skills extraction

&#x20;  - Reasoning for each match

&#x20;  - Relevant excerpt extraction





