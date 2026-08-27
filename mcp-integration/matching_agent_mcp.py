"""
Matching Agent with MCP Integration
Refactored agent using Model Context Protocol for resource management.
Replaces direct filesystem tools with MCP server communication.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from anthropic import Anthropic

from mcp_client_integration import MCPClient, MCPResourceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client_anthropic = Anthropic()


@dataclass
class MCPMatchingAgentState:
    """Agent state with MCP integration"""
    current_jd: Optional[str] = None
    jd_title: Optional[str] = None
    jd_company: Optional[str] = None
    jd_location: Optional[str] = None

    must_have_requirements: List[str] = field(default_factory=list)
    nice_to_have_requirements: List[str] = field(default_factory=list)

    resume_uris: List[str] = field(default_factory=list)
    matched_candidates: List[Dict] = field(default_factory=list)
    shortlisted_candidates: List[Dict] = field(default_factory=list)

    current_batch_job_id: Optional[str] = None
    conversation_history: List[Dict] = field(default_factory=list)

    mcp_server_info: Optional[Dict] = None


class MCPMatchingAgent:
    """
    Matching Agent with MCP Integration.
    Uses MCP server for resource management instead of direct file operations.
    """

    def __init__(self, mcp_client: MCPClient):
        """
        Initialize agent with MCP client.

        Args:
            mcp_client: Connected MCPClient instance
        """
        self.mcp_client = mcp_client
        self.resource_manager = MCPResourceManager(mcp_client)
        self.state = MCPMatchingAgentState()
        self.conversation_history = []

        logger.info("MCP Matching Agent initialized")

    async def initialize(self) -> None:
        """Initialize agent - get server info and list resources."""
        try:
            # Get server capabilities
            info = await self.mcp_client.get_info()
            self.state.mcp_server_info = info
            logger.info(f"Connected to MCP Server: {info['name']} v{info['version']}")

            # Discover available resumes
            resumes = await self.resource_manager.get_resumes()
            self.state.resume_uris = [r.uri for r in resumes]
            logger.info(f"Discovered {len(resumes)} resumes")

        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise

    async def process_job_description(self, jd_text: str) -> Dict[str, Any]:
        """
        Process job description using Claude.

        Args:
            jd_text: Job description text

        Returns:
            Extracted JD details
        """
        self.state.current_jd = jd_text

        # Use Claude to parse JD
        prompt = f"""
Extract the following information from this job description:
1. Job Title
2. Company Name
3. Location
4. Must-Have Requirements (list 5-10)
5. Nice-to-Have Requirements (list 3-5)

Job Description:
{jd_text}

Respond in JSON format:
{{
    "title": "...",
    "company": "...",
    "location": "...",
    "must_have": [...],
    "nice_to_have": [...]
}}
"""

        response = client_anthropic.messages.create(
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        try:
            result_text = response.content[0].text
            # Extract JSON
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            json_str = result_text[start_idx:end_idx]
            result = json.loads(json_str)

            # Update state
            self.state.jd_title = result.get("title")
            self.state.jd_company = result.get("company")
            self.state.jd_location = result.get("location")
            self.state.must_have_requirements = result.get("must_have", [])
            self.state.nice_to_have_requirements = result.get("nice_to_have", [])

            logger.info(f"Parsed JD: {self.state.jd_title} at {self.state.jd_company}")

            return {
                "title": self.state.jd_title,
                "company": self.state.jd_company,
                "location": self.state.jd_location,
                "must_have_count": len(self.state.must_have_requirements),
                "nice_to_have_count": len(self.state.nice_to_have_requirements)
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {str(e)}")
            return {"error": "Failed to parse job description"}

    async def search_candidates(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Search for matching candidates.

        Args:
            query: Search query
            top_k: Number of top candidates to return

        Returns:
            Search results
        """
        logger.info(f"Searching for candidates matching: {query}")

        # In production, this would use ChromaDB with MCP
        # For now, we'll use Claude to score resumes

        try:
            # Read all resume content
            resume_contents = []
            for uri in self.state.resume_uris[:top_k]:
                try:
                    content = await self.resource_manager.get_resume_content(uri)
                    resume_contents.append({
                        "uri": uri,
                        "content": content[:500]  # First 500 chars
                    })
                except Exception as e:
                    logger.warning(f"Failed to read resume {uri}: {str(e)}")

            # Use Claude to score resumes
            if not resume_contents:
                return {"status": "no_candidates"}

            scoring_prompt = f"""
Score these resumes against the job requirements.
Requirements: {', '.join(self.state.must_have_requirements)}

For each resume, provide a match score (0-100%).

Resumes:
{json.dumps(resume_contents[:5], indent=2)}

Respond in JSON format:
{{
    "candidates": [
        {{"uri": "...", "name": "...", "score": 85, "reasoning": "..."}}
    ]
}}
"""

            response = client_anthropic.messages.create(
                model="claude-opus-4-6",
                max_tokens=1000,
                messages=[{"role": "user", "content": scoring_prompt}]
            )

            result_text = response.content[0].text
            start_idx = result_text.find("{")
            end_idx = result_text.rfind("}") + 1
            json_str = result_text[start_idx:end_idx]
            result = json.loads(json_str)

            self.state.matched_candidates = result.get("candidates", [])

            return {
                "status": "success",
                "candidates_found": len(self.state.matched_candidates),
                "candidates": self.state.matched_candidates[:top_k]
            }

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def start_batch_index(self) -> Dict[str, Any]:
        """
        Start batch indexing of resumes using MCP.

        Returns:
            Batch job information
        """
        if not self.state.resume_uris:
            return {"status": "no_resumes"}

        try:
            job_id = await self.resource_manager.index_resumes(
                self.state.resume_uris
            )
            self.state.current_batch_job_id = job_id

            logger.info(f"Started batch index job: {job_id}")

            return {
                "status": "queued",
                "jobId": job_id,
                "resume_count": len(self.state.resume_uris)
            }

        except Exception as e:
            logger.error(f"Batch indexing failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def check_batch_status(self) -> Dict[str, Any]:
        """Check status of batch job."""
        if not self.state.current_batch_job_id:
            return {"status": "no_job"}

        try:
            status = await self.mcp_client.batch_status(
                self.state.current_batch_job_id
            )
            return status

        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def run_workflow(self, jd_text: str) -> Dict[str, Any]:
        """
        Run complete matching workflow.

        Args:
            jd_text: Job description text

        Returns:
            Workflow results
        """
        logger.info("Starting matching workflow...")

        try:
            # Step 1: Process JD
            jd_result = await self.process_job_description(jd_text)
            if "error" in jd_result:
                return {"status": "failed", "step": "parse_jd", "error": jd_result["error"]}

            # Step 2: Start batch indexing
            batch_result = await self.start_batch_index()

            # Step 3: Search candidates
            search_query = " ".join(self.state.must_have_requirements[:5])
            search_result = await self.search_candidates(search_query)

            # Step 4: Rank and shortlist
            self.state.shortlisted_candidates = sorted(
                self.state.matched_candidates,
                key=lambda x: x.get("score", 0),
                reverse=True
            )[:5]

            return {
                "status": "success",
                "jd_parsed": jd_result,
                "batch_job": batch_result,
                "search_results": search_result,
                "shortlisted_count": len(self.state.shortlisted_candidates),
                "shortlisted": self.state.shortlisted_candidates
            }

        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def watch_for_new_resumes(self) -> str:
        """
        Start watching for new resumes in directory.

        Returns:
            Watcher ID
        """
        try:
            watcher_id = await self.resource_manager.watch_resume_directory()
            logger.info(f"Started watching for new resumes: {watcher_id}")
            return watcher_id

        except Exception as e:
            logger.error(f"Watch failed: {str(e)}")
            raise

    async def get_agent_summary(self) -> Dict[str, Any]:
        """Get current agent state summary."""
        return {
            "current_jd": self.state.jd_title,
            "company": self.state.jd_company,
            "location": self.state.jd_location,
            "requirements": {
                "must_have": len(self.state.must_have_requirements),
                "nice_to_have": len(self.state.nice_to_have_requirements)
            },
            "candidates": {
                "total_discovered": len(self.state.resume_uris),
                "matched": len(self.state.matched_candidates),
                "shortlisted": len(self.state.shortlisted_candidates)
            },
            "active_batch_job": self.state.current_batch_job_id,
            "mcp_server": self.state.mcp_server_info
        }


# ==================== MAIN ENTRY POINT ====================

async def main():
    """Example usage of MCP Matching Agent."""
    # Create MCP client
    client = MCPClient.from_command("python filesystem_mcp_server.py")
    await asyncio.sleep(1)

    # Create agent
    agent = MCPMatchingAgent(client)
    await agent.initialize()

    # Example JD
    sample_jd = """
    Senior Backend Engineer - Python FastAPI
    
    Company: TechCorp
    Location: Remote
    
    Requirements:
    - 5+ years backend development
    - Expert Python skills
    - FastAPI framework experience
    - PostgreSQL and Redis expertise
    - Docker and Kubernetes knowledge
    - AWS cloud platform
    
    Nice-to-have:
    - GraphQL experience
    - Message queue systems
    """

    # Run workflow
    print("🚀 Running matching workflow...")
    result = await agent.run_workflow(sample_jd)

    print("\n📊 Results:")
    print(json.dumps(result, indent=2))

    # Get summary
    summary = await agent.get_agent_summary()
    print("\n📈 Agent Summary:")
    print(json.dumps(summary, indent=2))

    # Cleanup
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
