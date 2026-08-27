# MCP Integration: Agentic Profile Matching

**Model Context Protocol Integration for Standardized AI Agent Tool Management**

## 🎯 Project Overview

This project refactors the Day 1-2 agentic profile matching system to use the **Model Context Protocol (MCP)** instead of direct filesystem tools. It demonstrates how to build production-ready AI agents using standardized, interoperable tool interfaces.

### Key Achievements

- ✅ **JSON-RPC 2.0 Compliant MCP Server** (450+ lines)
- ✅ **High-Level MCP Client** (350+ lines)
- ✅ **Refactored Agent with MCP Integration** (350+ lines)
- ✅ **Comprehensive Test Suite** (6 test scenarios, 400+ lines)
- ✅ **Complete Architecture Documentation** (State machine diagrams)
- ✅ **Production-Ready Implementation** (Error handling, async jobs, security)

---

## 📋 Project Structure

```
mcp-integration/
├── filesystem_mcp_server.py      # MCP Server implementation
├── mcp_client_integration.py     # MCP Client & resource manager
├── matching_agent_mcp.py         # Refactored agent with MCP
├── test_mcp_integration.py       # Test scenarios (6 tests)
├── STATE_MACHINE.md              # Architecture & workflow diagrams
├── DEMO_SCRIPT_MCP.md            # Video demo script
├── requirements_mcp.txt          # Python dependencies
└── README_MCP.md                 # This file
```

---

## 🏗️ Architecture

### Component Layer Diagram

```
┌─────────────────────────────────────┐
│     STREAMLIT UI / CLIENT APP       │
│  (User Interface & Interaction)     │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│   MCP MATCHING AGENT (Refactored)   │
│  - Process JD (Claude)              │
│  - Search candidates (MCP)          │
│  - Batch indexing (MCP)             │
│  - Ranking & shortlisting           │
└─────────────┬───────────────────────┘
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
┌─────────────┐  ┌──────────────┐
│ MCP CLIENT  │  │ CLAUDE API   │
│ (JSON-RPC)  │  │ (Anthropic)  │
└──────┬──────┘  └──────────────┘
       │
       │ stdin/stdout
       │ JSON-RPC 2.0
       │
       ▼
┌─────────────────────────────────────┐
│  MCP FILESYSTEM SERVER              │
│  - Resource discovery               │
│  - File read/write/delete           │
│  - Directory watching               │
│  - Batch processing                 │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│     FILESYSTEM & RESOURCES          │
│  - ./data/resumes/                  │
│  - ./data/jobs/                     │
│  - ./chroma_data/                   │
└─────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the project
cd agentic-profile-matching

# Install dependencies
pip install -r requirements_mcp.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-proj-...
```

### 2. Start MCP Server

```bash
python filesystem_mcp_server.py
```

**Output:**
```
🚀 MCP Server running on stdin/stdout
Waiting for JSON-RPC 2.0 requests...
```

### 3. Run Tests

```bash
python test_mcp_integration.py
```

**Output:**
```
TEST 1: Server Connection & Capabilities ✅ PASSED
TEST 2: Resource Discovery ✅ PASSED
TEST 3: File Operations (Read/Write) ✅ PASSED
TEST 4: Batch Processing ✅ PASSED
TEST 5: Directory Watching ✅ PASSED
TEST 6: Agent Workflow (MCP Integration) ✅ PASSED

Total: 6 | Passed: 6 | Failed: 0
```

### 4. Run Agent Workflow

```python
import asyncio
from mcp_client_integration import MCPClient
from matching_agent_mcp import MCPMatchingAgent

async def main():
    # Create client and agent
    client = MCPClient.from_command("python filesystem_mcp_server.py")
    agent = MCPMatchingAgent(client)
    await agent.initialize()
    
    # Process job description
    jd = """
    Senior Backend Engineer - Python FastAPI
    Company: TechCorp
    ...
    """
    
    result = await agent.run_workflow(jd)
    print(result)

asyncio.run(main())
```

---

## 📚 Core Components

### 1. MCP Server (`filesystem_mcp_server.py`)

**Implements JSON-RPC 2.0 Protocol**

```python
Methods:
- resources/list              # List all resources (with optional type filter)
- resources/read              # Read resource content by URI
- resources/write             # Write to resource (with overwrite control)
- resources/delete            # Delete resource
- directory/watch             # Monitor directory for changes
- directory/unwatch           # Stop monitoring
- batch/process               # Process multiple files
- batch/status                # Check batch job status
- server/capabilities         # Get server capabilities
- server/info                 # Get server information
```

**Features:**
- ✅ JSON-RPC 2.0 compliant
- ✅ Standard error codes
- ✅ Resource discovery with URIs
- ✅ Async batch processing with job queue
- ✅ Directory watching with glob patterns
- ✅ Security: path validation, sandboxing
- ✅ Comprehensive error handling

### 2. MCP Client (`mcp_client_integration.py`)

**High-Level Async Client API**

```python
client = MCPClient.from_command("python filesystem_mcp_server.py")

# Resource operations
resources = await client.list_resources(resource_type="resume")
content = await client.read_resource("file:///path/to/resume.pdf")
await client.write_resource("file:///path", content, overwrite=True)
await client.delete_resource("file:///path")

# Batch operations
job_id = await client.batch_process("index", files, options)
status = await client.batch_status(job_id)
final = await client.wait_batch_completion(job_id)

# Directory watching
watcher_id = await client.watch_directory("file:///data/resumes", "*.pdf")
await client.unwatch_directory(watcher_id)

# Server info
caps = await client.get_capabilities()
info = await client.get_info()
```

### 3. Refactored Agent (`matching_agent_mcp.py`)

**Agentic Profile Matching with MCP Integration**

```python
agent = MCPMatchingAgent(mcp_client)
await agent.initialize()

# Process job description
await agent.process_job_description(jd_text)

# Search and rank candidates
search_result = await agent.search_candidates(query)

# Batch indexing
batch_result = await agent.start_batch_index()
status = await agent.check_batch_status()

# Complete workflow
workflow_result = await agent.run_workflow(jd_text)

# Watch for new resumes
watcher_id = await agent.watch_for_new_resumes()

# Get summary
summary = await agent.get_agent_summary()
```

---

## 🧪 Test Scenarios

### Test 1: Server Connection & Capabilities
**Verifies:** Server startup, capabilities listing, version info

### Test 2: Resource Discovery
**Verifies:** List resources, filter by type, URI generation

### Test 3: File Operations
**Verifies:** Read, write, delete operations with security checks

### Test 4: Batch Processing
**Verifies:** Async job submission, status tracking, completion

### Test 5: Directory Watching
**Verifies:** Watch setup, event tracking, unwatch

### Test 6: Agent Workflow
**Verifies:** End-to-end agent execution with MCP

---

## 🔄 Workflow: End-to-End

```
1. Initialize
   └─ Connect to MCP server
   └─ Discover resume resources
   └─ Get server capabilities

2. Process Job Description
   └─ Parse JD with Claude
   └─ Extract requirements (must-have & nice-to-have)
   └─ Classify requirements

3. Index Resumes (Async)
   └─ Start batch indexing job
   └─ Poll batch status
   └─ Wait for completion

4. Search Candidates
   └─ Read resume contents via MCP
   └─ Score with Claude
   └─ Rank by match score

5. Shortlist & Generate Report
   └─ Sort candidates
   └─ Select top-N
   └─ Generate hiring report

6. Interactive Refinement
   └─ Watch for new resumes (MCP watch)
   └─ Answer candidate questions
   └─ Provide explanations
```

---

## 🔐 Security

### Path Validation
```python
# All paths must be within base_path
base_path = Path("./data")
requested_path = Path("./data/resumes/resume.pdf")

# ✅ Allowed: within base_path
# ❌ Blocked: ../sensitive_data
# ❌ Blocked: /etc/passwd
```

### URI Format
```
file:///path/to/resource

Security:
- Relative paths converted to absolute
- All paths validated against base_path
- Symlink attacks prevented
- Directory traversal blocked
```

### Error Handling
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32002,
    "message": "Access denied",
    "data": {"path": "/etc/passwd"}
  },
  "id": 42
}
```

---

## 📊 JSON-RPC 2.0 Protocol

### Request Format
```json
{
  "jsonrpc": "2.0",
  "method": "resources/list",
  "params": {"type": "resume"},
  "id": 42
}
```

### Success Response
```json
{
  "jsonrpc": "2.0",
  "result": [...resources...],
  "id": 42
}
```

### Error Response
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params"
  },
  "id": 42
}
```

### Error Codes
| Code | Meaning |
|------|---------|
| -32700 | Parse error |
| -32600 | Invalid Request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |
| -32001 | Resource not found |
| -32002 | Access denied |
| -32003 | Operation failed |

---

## 🎬 Demo

### Recording Video
```bash
# Follow DEMO_SCRIPT_MCP.md
# 8-10 minutes total
# Silent with text overlays
# Shows all components working together
```

### Key Demo Scenes
1. MCP Server startup
2. Client connection
3. Resource discovery
4. JSON-RPC protocol
5. Batch processing
6. Agent workflow
7. Error handling
8. Test results

---

## 📈 Benefits of MCP

### Before (Day 1-2)
❌ Custom filesystem tools
❌ Ad-hoc implementations
❌ Inconsistent interfaces
❌ Hard to extend
❌ Difficult to test

### After (MCP Integration)
✅ Standardized JSON-RPC 2.0
✅ Proven protocol
✅ Consistent interfaces
✅ Easy to extend (add DB, web, etc.)
✅ Built-in error handling
✅ Interoperable with other tools
✅ Production-proven

---

## 🔧 Extensibility

### Add New MCP Servers

**Example: Database MCP Server**
```python
class DatabaseMCPServer:
    async def handle_request(self, request):
        if request.method == "query/execute":
            return await self.execute_query(request.params)
        # ... other methods
```

**Connect Multiple Servers**
```python
agent = MCPMatchingAgent(
    filesystem_client,    # Filesystem resources
    database_client,      # Query execution
    web_search_client,    # Web search
    email_client          # Email operations
)
```

---

## 📝 File Guide

| File | Lines | Purpose |
|------|-------|---------|
| `filesystem_mcp_server.py` | 450+ | Core MCP server implementation |
| `mcp_client_integration.py` | 350+ | Client API & resource manager |
| `matching_agent_mcp.py` | 350+ | Refactored agent using MCP |
| `test_mcp_integration.py` | 400+ | Comprehensive test scenarios |
| `STATE_MACHINE.md` | 200+ | Architecture diagrams & docs |
| `DEMO_SCRIPT_MCP.md` | 250+ | Video demo script |
| `requirements_mcp.txt` | 25 | Python dependencies |
| `README_MCP.md` | 400+ | This documentation |

**Total:** 2,400+ lines of code & documentation

---

## 🚀 Production Deployment

### Prerequisites
```bash
# Python 3.9+
python --version

# Dependencies installed
pip install -r requirements_mcp.txt

# API keys configured
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-proj-...
```

### Running in Production
```bash
# Start MCP server (background)
python filesystem_mcp_server.py &

# Start agent workflow
python matching_agent_mcp.py

# Or integrate with Streamlit UI
streamlit run app_streamlit.py
```

### Monitoring
```bash
# Check server health
curl localhost:8501/api/health

# View logs
tail -f server.log

# Monitor resources
python monitor_mcp.py
```

---

## 📖 Documentation

- **STATE_MACHINE.md** - Architecture diagrams, data flow, workflow
- **DEMO_SCRIPT_MCP.md** - Video recording guide (8-10 min demo)
- **Code Comments** - Inline documentation in all Python files

---

## ✅ Deliverables Checklist

- [x] MCP Server implementation (JSON-RPC 2.0)
- [x] MCP Client with high-level API
- [x] Refactored agent with MCP integration
- [x] `watch_directory()` capability
- [x] `batch_process()` capability
- [x] Comprehensive test suite (6 tests)
- [x] State machine documentation
- [x] Demo video script
- [x] Production-ready error handling
- [x] Security validation (path checks)

---

## 🎓 Learning Outcomes

After completing this project, you'll understand:

1. **Model Context Protocol (MCP)** - Standardized tool integration
2. **JSON-RPC 2.0** - Industry standard RPC protocol
3. **Agent Architecture** - Building extensible AI systems
4. **Async Python** - Async/await patterns for I/O
5. **Protocol Design** - Designing robust tool interfaces
6. **Error Handling** - Comprehensive error management
7. **Testing** - Test scenarios for complex systems
8. **Production Readiness** - Building production systems

---

## 🔗 Related Projects

- **Day 1:** Agent Architecture with Claude + LangGraph
- **Day 2:** Resume Search, Ranking, Multi-Round Screening
- **Day 3:** Streamlit UI + Interactive Chat
- **Day 4 (This):** MCP Integration + Standardization

---

## 📞 Support

For issues or questions:
1. Check STATE_MACHINE.md for architecture details
2. Review test_mcp_integration.py for examples
3. Check error codes in MCP protocol section
4. Review inline code comments

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** August 2026  

---

*Model Context Protocol Integration - Bringing Standardization to AI Agent Tooling*
