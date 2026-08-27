"""
MCP Client Integration
JSON-RPC 2.0 client for communicating with MCP servers.
Provides high-level API for agent to interact with MCP resources.
"""

import json
import asyncio
import subprocess
import sys
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPResource:
    """Resource returned by MCP server"""
    uri: str
    name: str
    description: str
    mimeType: str
    type: str
    metadata: Dict[str, Any]
    lastModified: Optional[str] = None
    size: Optional[int] = None


class MCPClient:
    """
    MCP JSON-RPC 2.0 Client.
    Communicates with MCP servers over stdin/stdout.
    """

    def __init__(self, server_process: Optional[subprocess.Popen] = None):
        """
        Initialize MCP client.

        Args:
            server_process: Subprocess running MCP server
        """
        self.server_process = server_process
        self.request_id = 0

    @classmethod
    def from_command(cls, command: str) -> "MCPClient":
        """
        Create client and start server process.

        Args:
            command: Command to start MCP server

        Returns:
            MCPClient instance
        """
        # Windows-compatible subprocess creation
        creationflags = 0
        if sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW
        
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            bufsize=1,
            creationflags=creationflags
        )
        return cls(server_process=process)

    async def call(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call MCP method.

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            Result from server
        """
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id
        }

        try:
            # Send request
            request_json = json.dumps(request)
            self.server_process.stdin.write(request_json + "\n")
            self.server_process.stdin.flush()

            # Read response
            response_line = self.server_process.stdout.readline()
            if not response_line:
                raise RuntimeError("Server closed connection")

            response = json.loads(response_line)

            # Check for errors
            if "error" in response and response["error"]:
                raise RuntimeError(
                    f"RPC Error {response['error']['code']}: "
                    f"{response['error']['message']}"
                )

            return response.get("result", {})

        except Exception as e:
            logger.error(f"RPC call failed: {str(e)}")
            raise

    async def list_resources(self, resource_type: Optional[str] = None) -> List[MCPResource]:
        """
        List all available resources.

        Args:
            resource_type: Optional type filter (file, directory, resume, index)

        Returns:
            List of resources
        """
        params = {}
        if resource_type:
            params["type"] = resource_type

        result = await self.call("resources/list", params)
        resources = result if isinstance(result, list) else []

        return [MCPResource(**r) for r in resources]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read resource content.

        Args:
            uri: Resource URI (e.g., "file:///path/to/file")

        Returns:
            Resource content and metadata
        """
        return await self.call("resources/read", {"uri": uri})

    async def write_resource(
        self,
        uri: str,
        content: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Write to resource.

        Args:
            uri: Resource URI
            content: Content to write
            overwrite: Overwrite if exists

        Returns:
            Operation result
        """
        return await self.call(
            "resources/write",
            {
                "uri": uri,
                "content": content,
                "overwrite": overwrite
            }
        )

    async def delete_resource(self, uri: str) -> Dict[str, Any]:
        """
        Delete resource.

        Args:
            uri: Resource URI

        Returns:
            Operation result
        """
        return await self.call("resources/delete", {"uri": uri})

    async def watch_directory(
        self,
        uri: str,
        pattern: str = "*"
    ) -> str:
        """
        Start watching directory for changes.

        Args:
            uri: Directory URI
            pattern: Glob pattern for files to watch

        Returns:
            Watcher ID
        """
        result = await self.call(
            "directory/watch",
            {"uri": uri, "pattern": pattern}
        )
        return result.get("watcherId")

    async def unwatch_directory(self, watcher_id: str) -> Dict[str, Any]:
        """
        Stop watching directory.

        Args:
            watcher_id: Watcher ID from watch_directory

        Returns:
            Operation result
        """
        return await self.call(
            "directory/unwatch",
            {"watcherId": watcher_id}
        )

    async def batch_process(
        self,
        operation: str,
        files: List[str],
        options: Optional[Dict] = None
    ) -> str:
        """
        Process multiple files in batch.

        Args:
            operation: Operation type (extract_text, validate_resume, index)
            files: List of file URIs
            options: Operation options

        Returns:
            Batch job ID
        """
        result = await self.call(
            "batch/process",
            {
                "operation": operation,
                "files": files,
                "options": options or {}
            }
        )
        return result.get("jobId")

    async def batch_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get batch job status.

        Args:
            job_id: Job ID from batch_process

        Returns:
            Job status and results
        """
        return await self.call("batch/status", {"jobId": job_id})

    async def wait_batch_completion(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Wait for batch job to complete.

        Args:
            job_id: Job ID
            timeout: Maximum wait time in seconds

        Returns:
            Final job status
        """
        start_time = datetime.now()

        while True:
            status = await self.batch_status(job_id)

            if status.get("status") in ["completed", "failed"]:
                return status

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Batch job {job_id} timed out")

            await asyncio.sleep(1)

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return await self.call("server/capabilities")

    async def get_info(self) -> Dict[str, Any]:
        """Get server information."""
        return await self.call("server/info")

    async def close(self) -> None:
        """Close server connection."""
        if self.server_process:
            self.server_process.stdin.close()
            self.server_process.wait()
            logger.info("MCP Server connection closed")


class MCPResourceManager:
    """
    High-level resource manager for MCP resources.
    Provides convenient methods for common operations.
    """

    def __init__(self, client: MCPClient):
        """
        Initialize resource manager.

        Args:
            client: MCPClient instance
        """
        self.client = client

    async def get_resumes(self) -> List[MCPResource]:
        """Get all resume resources."""
        return await self.client.list_resources(resource_type="resume")

    async def get_resume_content(self, uri: str) -> str:
        """Get resume content by URI."""
        result = await self.client.read_resource(uri)
        return result.get("content", "")

    async def index_resumes(self, resume_uris: List[str]) -> str:
        """
        Index multiple resumes in batch.

        Args:
            resume_uris: List of resume URIs

        Returns:
            Batch job ID
        """
        return await self.client.batch_process(
            operation="index",
            files=resume_uris
        )

    async def extract_resume_text(self, resume_uris: List[str]) -> str:
        """
        Extract text from multiple resumes.

        Args:
            resume_uris: List of resume URIs

        Returns:
            Batch job ID
        """
        return await self.client.batch_process(
            operation="extract_text",
            files=resume_uris
        )

    async def validate_resumes(self, resume_uris: List[str]) -> str:
        """
        Validate multiple resumes.

        Args:
            resume_uris: List of resume URIs

        Returns:
            Batch job ID
        """
        return await self.client.batch_process(
            operation="validate_resume",
            files=resume_uris
        )

    async def watch_resume_directory(self) -> str:
        """
        Watch for new resumes in directory.

        Returns:
            Watcher ID
        """
        return await self.client.watch_directory(
            uri="file://./data/resumes",
            pattern="*.pdf"
        )


# ==================== HELPER FUNCTIONS ====================

async def create_mcp_client() -> MCPClient:
    """
    Create and initialize MCP client.

    Returns:
        Connected MCPClient instance
    """
    client = MCPClient.from_command("python filesystem_mcp_server.py")
    await asyncio.sleep(1)  # Wait for server to start

    logger.info("MCP Client initialized")
    return client


async def example_usage():
    """Example usage of MCP client."""
    client = await create_mcp_client()

    try:
        # Get server info
        info = await client.get_info()
        print(f"Connected to: {info['name']}")

        # List resources
        resources = await client.list_resources()
        print(f"Found {len(resources)} resources")

        # Get capabilities
        caps = await client.get_capabilities()
        print(f"Capabilities: {caps['methods']}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())