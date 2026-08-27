# MCP Agent State Machine & Architecture

## Agent State Machine

```
┌─────────────┐
│   IDLE      │  Initial state - waiting for input
└──────┬──────┘
       │
       │ process_job_description(jd_text)
       ▼
┌─────────────────────────────────┐
│  PARSING_JD                     │  Claude parses JD
│  - Extract title, company       │  - Identify requirements
│  - Requirements extraction      │  - Classify must-have vs nice-to-have
└──────┬──────────────────────────┘
       │
       │ ✅ JD parsed
       ▼
┌─────────────────────────────────┐
│  DISCOVERING_RESOURCES          │  MCP: List all resumes
│  - Query MCP server             │  - Identify resume URIs
│  - Enumerate resume URIs        │  - Count total resources
└──────┬──────────────────────────┘
       │
       │ ✅ Resources discovered
       ▼
┌─────────────────────────────────┐
│  BATCH_INDEXING                 │  MCP: Batch process
│  - Start batch indexing job     │  - Index resumes
│  - Wait for completion          │  - Track job status
└──────┬──────────────────────────┘
       │
       │ ✅ Batch job completed
       ▼
┌─────────────────────────────────┐
│  SEARCHING                      │  Claude: Score candidates
│  - Search for matching resumes  │  - Hybrid matching
│  - Claude ranks candidates      │  - Gap analysis
└──────┬──────────────────────────┘
       │
       │ ✅ Candidates found
       ▼
┌─────────────────────────────────┐
│  RANKING                        │  Sort & filter
│  - Sort by match score          │  - Identify top candidates
│  - Shortlist top N              │  - Prepare shortlist
└──────┬──────────────────────────┘
       │
       │ ✅ Candidates ranked
       ▼
┌─────────────────────────────────┐
│  READY                          │  Awaiting user interaction
│  - Report ready                 │  - Chat ready
│  - Results available            │  - Watching for new resumes
└──────┬──────────────────────────┘
       │
       │ watch_for_new_resumes()
       ▼
┌─────────────────────────────────┐
│  WATCHING                       │  MCP: Directory watch
│  - Monitor directory            │  - Detect new resumes
│  - Auto-re-index                │  - Update candidate list
└─────────────────────────────────┘
```

---

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      STREAMLIT UI / CLIENT                        │
│                    (User Interface Layer)                         │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │ Input: JD
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    MCP MATCHING AGENT                             │
│                   (Orchestration Layer)                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ State Management:                                          │ │
│  │ - current_jd, jd_title, company, location                │ │
│  │ - must_have_requirements, nice_to_have_requirements       │ │
│  │ - resume_uris, matched_candidates, shortlisted_candidates│ │
│  │ - current_batch_job_id                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Methods:                                                   │ │
│  │ - process_job_description() → Claude API                  │ │
│  │ - search_candidates() → Claude API                        │ │
│  │ - start_batch_index() → MCP Client                        │ │
│  │ - check_batch_status() → MCP Client                       │ │
│  │ - watch_for_new_resumes() → MCP Client                   │ │
│  │ - run_workflow() → Orchestrates all steps                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────┬──────────────────────────┬────────────────────────────────┘
       │                          │
       │ JSON-RPC 2.0 Calls       │ OpenAI API Calls
       │                          │
       ▼                          ▼
┌──────────────────────────┐  ┌──────────────────┐
│   MCP CLIENT             │  │  CLAUDE API      │
│   (JSON-RPC 2.0)         │  │  (Anthropic)     │
│                          │  │                  │
│ - list_resources()       │  │ - Parse JD       │
│ - read_resource()        │  │ - Score resumes  │
│ - write_resource()       │  │ - Rank candidates│
│ - delete_resource()      │  │ - Generate Q&A   │
│ - batch_process()        │  └──────────────────┘
│ - batch_status()         │
│ - watch_directory()      │
│ - unwatch_directory()    │
└──────┬───────────────────┘
       │
       │ stdin/stdout
       │ (JSON-RPC)
       ▼
┌──────────────────────────────────────────────────────────────────┐
│           MCP FILESYSTEM SERVER                                   │
│           (Resource Management & Execution)                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Capabilities:                                            │   │
│  │ - File read/write/delete (secured)                       │   │
│  │ - Resource discovery (URI-based)                         │   │
│  │ - Directory watching (with glob patterns)                │   │
│  │ - Batch processing (async job queue)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Backend:                                                 │   │
│  │ - ./data/resumes/ ← Resume files                         │   │
│  │ - ./data/jobs/ ← Job descriptions                        │   │
│  │ - ./chroma_data/ ← Vector DB (optional)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: End-to-End

```
USER INPUT: Job Description
         ↓
         │ 1. Parse JD
         ├─→ Claude API
         ├─→ Extract: title, company, location, requirements
         ├─→ Classify: must-have vs nice-to-have
         ▼
MCP: List Resources
         ↓
         │ 2. Discover Resumes
         ├─→ MCP Client: list_resources(type="resume")
         ├─→ Get resume URIs (file://...resume.pdf)
         ▼
MCP: Batch Index
         ↓
         │ 3. Index & Process
         ├─→ MCP Client: batch_process(operation="index")
         ├─→ MCP Server: Execute indexing
         ├─→ MCP Client: batch_status(job_id)
         ▼
MCP: Read & Claude Score
         ↓
         │ 4. Search & Score
         ├─→ MCP Client: read_resource() for each resume
         ├─→ Claude API: Score candidates
         ├─→ Generate reasoning
         ▼
Sort & Shortlist
         ↓
         │ 5. Rank & Select
         ├─→ Sort by match score
         ├─→ Select top-N candidates
         ▼
Generate Results
         ↓
         │ 6. Output
         ├─→ Professional report
         ├─→ Candidate profiles
         ├─→ Interview questions
         ├─→ Ready for chat Q&A
         ▼
OUTPUT: Hiring Report + Candidate Matches
```

---

## MCP Protocol: Request/Response Cycle

```
┌─ AGENT ─────────────────────────────────────────────────────────┐
│                                                                  │
│  Construct JSON-RPC 2.0 Request:                               │
│  {                                                              │
│    "jsonrpc": "2.0",                                            │
│    "method": "resources/list",                                  │
│    "params": {"type": "resume"},                                │
│    "id": 42                                                     │
│  }                                                              │
│                                                                  │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      │ stdin.write() + flush()
                      ▼
┌─ MCP SERVER ────────────────────────────────────────────────────┐
│                                                                  │
│  Parse Request → Validate → Route to handler                   │
│                                                                  │
│  Handler: resources/list                                        │
│  1. Scan ./data/resumes/                                        │
│  2. Build resource objects                                      │
│  3. Return list                                                 │
│                                                                  │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      │ stdout.write() + flush()
                      ▼
┌─ AGENT ─────────────────────────────────────────────────────────┐
│                                                                  │
│  Receive JSON-RPC 2.0 Response:                                │
│  {                                                              │
│    "jsonrpc": "2.0",                                            │
│    "result": [                                                  │
│      {                                                          │
│        "uri": "file:///path/resume1.pdf",                       │
│        "name": "resume1.pdf",                                   │
│        "type": "resume",                                        │
│        "size": 125000,                                          │
│        "mimeType": "application/pdf"                            │
│      },                                                         │
│      ...                                                        │
│    ],                                                           │
│    "id": 42                                                     │
│  }                                                              │
│                                                                  │
│  Parse & Process Result → Update state                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

```
┌─────────────────────────────────────────────────────────────┐
│               JSON-RPC 2.0 Error Codes                      │
├─────────────────────────────────────────────────────────────┤
│  -32700  │ Parse error - Invalid JSON received             │
│  -32600  │ Invalid Request - Not valid JSON-RPC 2.0         │
│  -32601  │ Method not found                                 │
│  -32602  │ Invalid params                                   │
│  -32603  │ Internal error in server                         │
│  -32000  │ Custom server error (general)                    │
│  -32001  │ Resource not found                               │
│  -32002  │ Access denied                                    │
│  -32003  │ Operation failed                                 │
└─────────────────────────────────────────────────────────────┘

Error Response Format:
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "Expected 'uri' parameter"
    }
  },
  "id": 42
}
```

---

## Resource URI Scheme

```
file://path/to/resource

Examples:
- file:///data/resumes/john_doe.pdf
- file:///data/jobs/senior_engineer.txt
- file:///data/index/embeddings.json

Special:
- file:/// (root of base path)
- Paths must be within base_path for security
- Non-absolute paths converted to absolute
```

---

## Workflow Sequence

```
Agent              Client           Server
  │                 │                  │
  ├─ initialize()   │                  │
  │                 ├─ connect       ──→ ✅
  │                 │
  │                 ├─ get_info()    ──→ server info ──→
  │                 │
  │                 ├─ list_resources()
  │                 │                ──→ [resume URIs] ──→
  │
  ├─ process_jd()   │
  │   (Claude)      │
  │
  ├─ batch_process()│
  │                 ├─ batch/process ──→ start job ──→
  │                 │
  ├─ wait_batch()   │
  │                 ├─ batch/status ──→ progress ──→
  │                 ├─ batch/status ──→ progress ──→
  │                 ├─ batch/status ──→ complete ──→
  │
  ├─ search_candidates()
  │   (Claude)      │
  │
  ├─ rank()         │
  │
  ├─ run_workflow() │ Complete cycle
  │
  ├─ watch_for_new()│
  │                 ├─ directory/watch ──→ watcher_id ──→
  │                 │ (monitoring...)
  │
```

---

## Summary

- **Agent State**: Tracks JD, requirements, candidates, batch jobs
- **MCP Protocol**: JSON-RPC 2.0 over stdin/stdout
- **Security**: URI-based access control, path validation
- **Async**: Batch processing with status polling
- **Extensible**: Easy to add new MCP servers (web, DB, etc.)
