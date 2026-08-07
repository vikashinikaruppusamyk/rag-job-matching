\# RAG-Based Resume-to-Job Matching System



A semantic search system using Retrieval Augmented Generation (RAG) to match job descriptions with qualified candidates. Features intelligent document chunking, vector embeddings, ChromaDB storage, and hybrid search combining semantic similarity with keyword matching.



\*\*Live Demo:\*\* See `notebook.ipynb` for interactive examples.



\---



\## 📋 Features



✓ \*\*Smart Document Processing\*\*

\- Intelligent chunking preserving resume sections (Education, Experience, Skills, etc.)

\- Metadata extraction (Name, Years of Experience, Skills)

\- Support for PDF, DOCX, and TXT formats

\- Batch processing with error handling



✓ \*\*Vector Embeddings \& Storage\*\*

\- OpenAI embeddings (text-embedding-3-small, 1536-dimensional)

\- ChromaDB persistent storage

\- 333 embeddings from 30 diverse resumes

\- Fast cosine similarity search (<500ms)



✓ \*\*Hybrid Search \& Matching\*\*

\- Semantic similarity (vector-based, 70% weight)

\- Keyword matching (exact/fuzzy, 30% weight)

\- Combined scoring (0-100 scale)

\- Must-have requirement filtering



✓ \*\*Production-Ready Output\*\*

\- JSON format per specification

\- Match scores with confidence levels

\- Relevant skill extraction

\- Reasoning for each match

\- Resume excerpt extraction



\---



\## 🏗️ Architecture



┌─────────────────────────────────────────────────────────────┐

│ INPUT LAYER │

│ • 30 Resumes (diverse roles, 3-10 years experience) │

│ • 5 Job Descriptions (Backend, ML, DevOps, Full Stack) │

└─────────────────────────────────────────────────────────────┘

↓

┌─────────────────────────────────────────────────────────────┐

│ PROCESSING LAYER │

│ • Smart Chunking (preserve sections) │

│ • Metadata Extraction (name, years, skills) │

│ • OpenAI Embeddings (1536-dim vectors) │

└─────────────────────────────────────────────────────────────┘

↓

┌─────────────────────────────────────────────────────────────┐

│ STORAGE LAYER │

│ • ChromaDB (persistent ./chroma\_data/) │

│ • 333 embeddings indexed │

│ • Metadata stored alongside vectors │

└─────────────────────────────────────────────────────────────┘

↓

┌─────────────────────────────────────────────────────────────┐

│ RETRIEVAL LAYER │

│ • Semantic Search (cosine similarity) │

│ • Keyword Extraction (from JD) │

│ • Hybrid Scoring (70% semantic + 30% keyword) │

└─────────────────────────────────────────────────────────────┘

↓

┌─────────────────────────────────────────────────────────────┐

│ OUTPUT LAYER │

│ • Top-10 Matches (scored 0-100) │

│ • Matched Skills Extraction │

│ • Reasoning \& Explanations │

│ • JSON Output │

└─────────────────────────────────────────────────────────────┘





\---



\## 📊 Performance Metrics



| Metric | Value |

|--------|-------|

| \*\*Total Resumes\*\* | 30 |

| \*\*Total Embeddings\*\* | 333 |

| \*\*Avg Chunks/Resume\*\* | 11 |

| \*\*Job Descriptions Tested\*\* | 5 |

| \*\*Total Matches Analyzed\*\* | 49 |

| \*\*Avg Match Score\*\* | 57.5/100 |

| \*\*Highest Score\*\* | 76.7/100 |

| \*\*Lowest Score\*\* | 44.9/100 |

| \*\*Avg Skills Matched\*\* | 3.8 per candidate |

| \*\*Retrieval Latency\*\* | <500ms |



\### Sample Results by Role



| JD | Top Match | Score | Skills Matched |

|----|-----------|-------|-----------------|

| Backend Engineer | John Doe | 76.7 | 5 |

| ML Engineer | Frank Chen | 63.2 | 5 |

| DevOps Engineer | Jack Kumar | 68.2 | 5 |

| Full Stack Engineer | Henry Brown | 67.3 | 5 |

| Data Engineer | Grace Martinez C | 68.8 | 2 |



\---



\## 🚀 Quick Start



\### Prerequisites

\- Python 3.9+

\- OpenAI API key (get free at https://platform.openai.com/api/keys)

\- \~500MB disk space



\### Installation



```bash

\# Clone repository

git clone https://github.com/vikashinikaruppusamyk/rag-job-matching.git

cd rag-job-matching



\# Create virtual environment

python -m venv venv

source venv/bin/activate  # On Windows: venv\\Scripts\\activate



\# Install dependencies

pip install -r requirements.txt



\# Set up environment variables

echo "OPENAI\_API\_KEY=sk-your-key-here" > .env

echo "RESUME\_DATA\_PATH=./data/resumes" >> .env

echo "JD\_DATA\_PATH=./data/job\_descriptions" >> .env

```



\### Basic Usage



```python

from job\_matcher import run\_job\_matcher



\# Define a job description

jd = """

Senior Backend Engineer with 5+ years experience.

Required: Python, FastAPI, PostgreSQL, Docker, AWS

"""



\# Run the matcher

output = run\_job\_matcher(jd, top\_k=10, output\_file='matches.json')



\# Output format

\# {

\#     "job\_description": "...",

\#     "top\_matches": \[

\#         {

\#             "candidate\_name": "John Doe",

\#             "match\_score": 76.7,

\#             "matched\_skills": \["Python", "FastAPI", ...],

\#             "reasoning": "Strong match: ...",

\#             ...

\#         }

\#     ]

\# }

```



\---



\## 📁 Project Structure



rag-job-matching/

├── smart\_chunking.py # Section-aware document chunking

├── resume\_loader.py # Resume file loading

├── generate\_embeddings.py # Batch embedding generation

├── vector\_db.py # ChromaDB setup \& queries

├── hybrid\_matcher.py # Semantic + keyword search

├── job\_matcher.py # Main matching engine

├── generate\_metrics.py # Metrics report generation

│

├── data/

│ ├── resumes/ # 30 diverse resumes

│ └── job\_descriptions/ # 5 test job descriptions

│

├── chroma\_data/ # ChromaDB persistent storage

│

├── notebook.ipynb # Interactive Jupyter walkthrough

├── README.md # This file

├── requirements.txt # Python dependencies

├── .env # Environment variables (API keys)

│

├── output\_\*.json # Sample matcher outputs

├── METRICS\_REPORT.json # Performance metrics

└── DAY4\_TESTING\_SUMMARY.md # Testing documentation





\---



\## 🔧 Configuration



\### Hybrid Search Weights



Default: 70% semantic, 30% keyword



To adjust weights, edit `hybrid\_matcher.py`:



```python

hybrid\_search(

&#x20;   collection,

&#x20;   jd,

&#x20;   semantic\_weight=0.7,  # Adjust this

&#x20;   keyword\_weight=0.3    # Adjust this

)

```



\*\*Recommendations:\*\*

\- \*\*General roles\*\*: 70/30 (default) ✓

\- \*\*Technical roles\*\*: 80/20 (more semantic)

\- \*\*Specialist roles\*\*: 60/40 (more keyword-focused)



\### Must-Have Filtering



The system automatically extracts and filters:

\- Experience requirements (e.g., "5+ years")

\- Critical skills (e.g., "must know Python")



Configure in `hybrid\_matcher.py`:



```python

def apply\_must\_have\_filters(matches, jd):

&#x20;   # Edit regex patterns here

&#x20;   exp\_match = re.search(r'(\\d+)\\+?\\s\*years?', jd.lower())

&#x20;   ...

```



\---



\## 📚 How It Works



\### Step 1: Document Processing



Resume → Detect Sections → Smart Chunking → Extract Metadata





Example output:

\- Section: "Experience"

\- Chunk: "Senior Backend Engineer... 5 years..."

\- Metadata: {name: "John Doe", years: 6, skills: \["Python", "FastAPI"]}



\### Step 2: Embeddings



Chunk Text → OpenAI API → 1536-dimensional vector





\### Step 3: Storage



Vector + Metadata → ChromaDB → Persistent Index





\### Step 4: Hybrid Search



JD → Extract Keywords + Embed

Query Vector → Top-K Semantic Results

Rerank by Hybrid Score (semantic + keyword)

Filter by Must-Haves





\### Step 5: Output



Top-10 Matches → Score (0-100) → Reason → JSON





\---



\## 🧪 Testing



Run all tests:



```bash

\# Verify database

python verify\_pipeline.py



\# Generate metrics

python generate\_metrics.py



\# Interactive notebook

jupyter notebook notebook.ipynb

```



\---



\## 📝 Output Format



```json

{

&#x20; "job\_description": "Senior Backend Engineer...",

&#x20; "top\_matches": \[

&#x20;   {

&#x20;     "candidate\_name": "John Doe",

&#x20;     "resume\_path": "resumes/resume\_01\_john\_doe.txt",

&#x20;     "match\_score": 76.7,

&#x20;     "matched\_skills": \["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],

&#x20;     "relevant\_excerpts": \["Senior Backend Engineer at TechCorp... 5 years..."],

&#x20;     "reasoning": "Excellent match: Strong semantic alignment (85) with all critical keywords (95). 6+ years experience."

&#x20;   }

&#x20; ]

}

```



\---



\## 🚨 Known Limitations



1\. \*\*Dataset Size\*\*: 30 resumes (small sample)

&#x20;  - Mitigation: Results improve with larger dataset

&#x20;  

2\. \*\*Keyword Matching\*\*: Simple regex patterns

&#x20;  - Mitigation: Can upgrade to NLP-based entity extraction



3\. \*\*Resume Formats\*\*: Limited to text extraction

&#x20;  - Mitigation: PDF/DOCX parsing already implemented



4\. \*\*Language\*\*: English only

&#x20;  - Mitigation: OpenAI embeddings support 95+ languages



\---



\## 🔮 Future Improvements



\- \[ ] Fine-tune weights per domain/role

\- \[ ] Add fuzzy keyword matching

\- \[ ] Implement multi-language support

\- \[ ] Create web dashboard (Flask/React)

\- \[ ] Add candidate ranking by seniority

\- \[ ] Support video resume analysis

\- \[ ] Real-time notification system

\- \[ ] A/B testing framework for weights



\---



\## 📄 License



Open source. Feel free to use and modify.



\---



\## 👤 Author



\*\*Vikashini\*\* | Backend Developer | Bengaluru



GitHub: https://github.com/vikashinikaruppusamyk/rag-job-matching



\---



\## 🎯 Key Takeaways



✓ RAG is powerful for semantic search beyond keyword matching

✓ Hybrid approach combines best of both worlds

✓ Vector embeddings capture contextual meaning

✓ ChromaDB simplifies vector storage \& retrieval

✓ Scoring frameworks enable transparent matching



\*\*Ready to deploy. This is production-grade code.\*\* 🚀

