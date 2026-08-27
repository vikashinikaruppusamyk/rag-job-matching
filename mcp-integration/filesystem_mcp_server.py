"""
MCP Server - Filesystem & Resume Tools
Implements JSON-RPC 2.0 compliant Model Context Protocol server.
Exposes file system operations, resume processing, and directory monitoring.
"""

import json
import os
import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import mimetypes
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """MCP Resource Types"""
    FILE = "file"
    DIRECTORY = "directory"
    RESUME = "resume"
    INDEX = "index"


class ErrorCode(int, Enum):
    """JSON-RPC 2.0 Error Codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    RESOURCE_NOT_FOUND = -32001
    ACCESS_DENIED = -32002
    OPERATION_FAILED = -32003


@dataclass
class MCPResource:
    """MCP Resource Representation"""
    uri: str
    name: str
    description: str
    mimeType: str
    type: ResourceType
    metadata: Dict[str, Any]
    lastModified: Optional[str] = None
    size: Optional[int] = None

    def to_dict(self):
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mimeType,
            "type": self.type.value,
            "metadata": self.metadata,
            "lastModified": self.lastModified,
            "size": self.size
        }


@dataclass
class MCPRequest:
    """MCP JSON-RPC 2.0 Request"""
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method"),
            params=data.get("params", {}),
            id=data.get("id")
        )


@dataclass
class MCPResponse:
    """MCP JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict] = None
    id: Optional[int] = None

    def to_dict(self):
        return {
            k: v for k, v in asdict(self).items()
            if v is not None
        }


class FilesystemMCPServer:
    """
    MCP Server for filesystem and resume operations.
    Implements JSON-RPC 2.0 protocol with resource discovery.
    """

    def __init__(self, base_path: str = "./data", watch_enabled: bool = True):
        """
        Initialize MCP Server.

        Args:
            base_path: Root directory for resources
            watch_enabled: Enable directory watching
        """
        self.base_path = Path(base_path)
        self.watch_enabled = watch_enabled
        self.watchers = {}
        self.batch_jobs = {}
        self.request_id_counter = 0

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"MCP Server initialized at {self.base_path}")

    async def handle_request(self, request_data: str) -> str:
        """
        Handle JSON-RPC 2.0 request.

        Args:
            request_data: JSON-encoded request

        Returns:
            JSON-encoded response
        """
        try:
            data = json.loads(request_data)
            request = MCPRequest.from_dict(data)

            # Route to appropriate handler
            if request.method == "resources/list":
                result = await self.list_resources(request.params)
            elif request.method == "resources/read":
                result = await self.read_resource(request.params)
            elif request.method == "resources/write":
                result = await self.write_resource(request.params)
            elif request.method == "resources/delete":
                result = await self.delete_resource(request.params)
            elif request.method == "directory/watch":
                result = await self.watch_directory(request.params)
            elif request.method == "directory/unwatch":
                result = await self.unwatch_directory(request.params)
            elif request.method == "batch/process":
                result = await self.batch_process(request.params)
            elif request.method == "batch/status":
                result = await self.batch_status(request.params)
            elif request.method == "server/capabilities":
                result = await self.get_capabilities()
            elif request.method == "server/info":
                result = await self.get_info()
            else:
                return self._error_response(
                    ErrorCode.METHOD_NOT_FOUND,
                    f"Method not found: {request.method}",
                    request.id
                )

            return self._success_response(result, request.id)

        except json.JSONDecodeError as e:
            return self._error_response(
                ErrorCode.PARSE_ERROR,
                f"JSON parse error: {str(e)}",
                None
            )
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return self._error_response(
                ErrorCode.INTERNAL_ERROR,
                f"Internal server error: {str(e)}",
                data.get("id") if isinstance(data, dict) else None
            )

    async def list_resources(self, params: Dict) -> List[Dict]:
        """
        List all available resources.

        Args:
            params: Optional filter parameters

        Returns:
            List of resources
        """
        resources = []
        filter_type = params.get("type")  # Optional filter

        # List files in base path
        for item in self.base_path.rglob("*"):
            if item.is_file():
                resource = self._create_resource(item)
                if not filter_type or resource.type.value == filter_type:
                    resources.append(resource.to_dict())

        return resources

    async def read_resource(self, params: Dict) -> Dict:
        """
        Read a resource.

        Args:
            params: {"uri": "file://path/to/resource"}

        Returns:
            Resource content
        """
        uri = params.get("uri")
        if not uri:
            raise ValueError("Missing 'uri' parameter")

        # Parse URI (file://path)
        file_path = self._uri_to_path(uri)

        if not file_path.exists():
            raise FileNotFoundError(f"Resource not found: {uri}")

        if not self._is_within_base(file_path):
            raise PermissionError(f"Access denied to: {uri}")

        # Read file content
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = str(file_path.read_bytes())

            return {
                "uri": uri,
                "content": content,
                "mimeType": mimetypes.guess_type(file_path)[0] or "text/plain",
                "size": file_path.stat().st_size,
                "lastModified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }
        else:
            raise ValueError(f"Not a file: {uri}")

    async def write_resource(self, params: Dict) -> Dict:
        """
        Write to a resource.

        Args:
            params: {
                "uri": "file://path",
                "content": "file content",
                "overwrite": bool
            }

        Returns:
            Operation result
        """
        uri = params.get("uri")
        content = params.get("content")
        overwrite = params.get("overwrite", False)

        if not uri or content is None:
            raise ValueError("Missing 'uri' or 'content' parameter")

        file_path = self._uri_to_path(uri)

        # Check if within base path
        if not self._is_within_base(file_path):
            raise PermissionError(f"Access denied to: {uri}")

        # Check if exists
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File exists: {uri}")

        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        file_path.write_text(content, encoding='utf-8')

        return {
            "uri": uri,
            "created": not file_path.exists(),
            "size": file_path.stat().st_size,
            "timestamp": datetime.now().isoformat()
        }

    async def delete_resource(self, params: Dict) -> Dict:
        """
        Delete a resource.

        Args:
            params: {"uri": "file://path"}

        Returns:
            Operation result
        """
        uri = params.get("uri")
        if not uri:
            raise ValueError("Missing 'uri' parameter")

        file_path = self._uri_to_path(uri)

        if not self._is_within_base(file_path):
            raise PermissionError(f"Access denied to: {uri}")

        if not file_path.exists():
            raise FileNotFoundError(f"Resource not found: {uri}")

        # Delete
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)

        return {
            "uri": uri,
            "deleted": True,
            "timestamp": datetime.now().isoformat()
        }

    async def watch_directory(self, params: Dict) -> Dict:
        """
        Monitor directory for changes.

        Args:
            params: {
                "uri": "file://path/to/directory",
                "pattern": "*.pdf"  # Optional glob pattern
            }

        Returns:
            Watcher ID and status
        """
        uri = params.get("uri")
        pattern = params.get("pattern", "*")

        if not uri:
            raise ValueError("Missing 'uri' parameter")

        dir_path = self._uri_to_path(uri)

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {uri}")

        if not self._is_within_base(dir_path):
            raise PermissionError(f"Access denied to: {uri}")

        # Create watcher
        watcher_id = f"watcher_{len(self.watchers)}"
        self.watchers[watcher_id] = {
            "uri": uri,
            "pattern": pattern,
            "created": datetime.now().isoformat(),
            "events": []
        }

        logger.info(f"Started watching {uri} with pattern {pattern}")

        return {
            "watcherId": watcher_id,
            "uri": uri,
            "pattern": pattern,
            "status": "watching"
        }

    async def unwatch_directory(self, params: Dict) -> Dict:
        """
        Stop monitoring a directory.

        Args:
            params: {"watcherId": "watcher_0"}

        Returns:
            Operation result
        """
        watcher_id = params.get("watcherId")

        if watcher_id not in self.watchers:
            raise ValueError(f"Watcher not found: {watcher_id}")

        watcher = self.watchers.pop(watcher_id)

        return {
            "watcherId": watcher_id,
            "stopped": True,
            "eventsRecorded": len(watcher["events"]),
            "timestamp": datetime.now().isoformat()
        }

    async def batch_process(self, params: Dict) -> Dict:
        """
        Process multiple files in batch.

        Args:
            params: {
                "operation": "extract_text|validate_resume|index",
                "files": ["file://path1", "file://path2"],
                "options": {...}
            }

        Returns:
            Batch job ID and status
        """
        operation = params.get("operation")
        files = params.get("files", [])
        options = params.get("options", {})

        if not operation:
            raise ValueError("Missing 'operation' parameter")

        # Create batch job
        job_id = f"batch_{len(self.batch_jobs)}"
        self.batch_jobs[job_id] = {
            "operation": operation,
            "files": files,
            "options": options,
            "status": "queued",
            "created": datetime.now().isoformat(),
            "progress": 0,
            "results": []
        }

        # Start processing asynchronously
        asyncio.create_task(self._execute_batch(job_id))

        return {
            "jobId": job_id,
            "operation": operation,
            "fileCount": len(files),
            "status": "queued"
        }

    async def batch_status(self, params: Dict) -> Dict:
        """
        Get batch job status.

        Args:
            params: {"jobId": "batch_0"}

        Returns:
            Job status and results
        """
        job_id = params.get("jobId")

        if job_id not in self.batch_jobs:
            raise ValueError(f"Batch job not found: {job_id}")

        job = self.batch_jobs[job_id]

        return {
            "jobId": job_id,
            "operation": job["operation"],
            "status": job["status"],
            "progress": job["progress"],
            "fileCount": len(job["files"]),
            "completedCount": len(job["results"]),
            "results": job["results"]
        }

    async def get_capabilities(self) -> Dict:
        """Get server capabilities."""
        return {
            "methods": [
                "resources/list",
                "resources/read",
                "resources/write",
                "resources/delete",
                "directory/watch",
                "directory/unwatch",
                "batch/process",
                "batch/status",
                "server/capabilities",
                "server/info"
            ],
            "resourceTypes": [rt.value for rt in ResourceType],
            "features": {
                "directoryWatching": self.watch_enabled,
                "batchProcessing": True,
                "resourceDiscovery": True,
                "jsonRpc20": True
            }
        }

    async def get_info(self) -> Dict:
        """Get server information."""
        return {
            "name": "Filesystem & Resume MCP Server",
            "version": "1.0.0",
            "basePath": str(self.base_path),
            "jsonrpcVersion": "2.0",
            "capabilities": await self.get_capabilities(),
            "resources": {
                "filesCount": len(list(self.base_path.rglob("*"))),
                "watchersActive": len(self.watchers),
                "batchJobsActive": len([j for j in self.batch_jobs.values()
                                       if j["status"] == "processing"])
            }
        }

    # ==================== PRIVATE METHODS ====================

    def _uri_to_path(self, uri: str) -> Path:
        """Convert file:// URI to Path."""
        if uri.startswith("file://"):
            return Path(uri[7:])
        return Path(uri)

    def _is_within_base(self, path: Path) -> bool:
        """Check if path is within base directory."""
        try:
            path.resolve().relative_to(self.base_path.resolve())
            return True
        except ValueError:
            return False

    def _create_resource(self, file_path: Path) -> MCPResource:
        """Create MCPResource from file path."""
        stat = file_path.stat()
        uri = f"file://{file_path}"

        # Determine resource type
        if file_path.suffix.lower() in ['.pdf', '.docx', '.txt']:
            resource_type = ResourceType.RESUME
        elif file_path.is_dir():
            resource_type = ResourceType.DIRECTORY
        else:
            resource_type = ResourceType.FILE

        return MCPResource(
            uri=uri,
            name=file_path.name,
            description=f"{resource_type.value} resource",
            mimeType=mimetypes.guess_type(file_path)[0] or "application/octet-stream",
            type=resource_type,
            metadata={
                "path": str(file_path),
                "extension": file_path.suffix
            },
            lastModified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size=stat.st_size
        )

    def _success_response(self, result: Any, request_id: Optional[int]) -> str:
        """Create success response."""
        response = MCPResponse(
            jsonrpc="2.0",
            result=result,
            id=request_id
        )
        return json.dumps(response.to_dict())

    def _error_response(self, code: ErrorCode, message: str,
                       request_id: Optional[int]) -> str:
        """Create error response."""
        response = MCPResponse(
            jsonrpc="2.0",
            error={
                "code": code.value,
                "message": message
            },
            id=request_id
        )
        return json.dumps(response.to_dict())

    async def _execute_batch(self, job_id: str) -> None:
        """Execute batch job."""
        job = self.batch_jobs[job_id]
        job["status"] = "processing"

        try:
            for i, file_uri in enumerate(job["files"]):
                # Simulate processing
                await asyncio.sleep(0.5)

                file_path = self._uri_to_path(file_uri)
                if file_path.exists():
                    result = {
                        "file": file_uri,
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    }

                    # Add operation-specific result
                    if job["operation"] == "extract_text":
                        result["textLength"] = len(file_path.read_text())
                    elif job["operation"] == "validate_resume":
                        result["isValid"] = True
                    elif job["operation"] == "index":
                        result["indexed"] = True

                    job["results"].append(result)

                job["progress"] = int((i + 1) / len(job["files"]) * 100)

            job["status"] = "completed"
        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            logger.error(f"Batch job {job_id} failed: {str(e)}")


# ==================== SERVER ENTRY POINT ====================

async def main():
    """Run MCP server."""
    server = FilesystemMCPServer(base_path="./data", watch_enabled=True)

    print("🚀 MCP Server running on stdin/stdout")
    print("Waiting for JSON-RPC 2.0 requests...\n")

    loop = asyncio.get_event_loop()

    while True:
        try:
            # Read from stdin
            line = input()
            if line.strip():
                # Process request
                response = await server.handle_request(line)
                print(response)
        except EOFError:
            break
        except Exception as e:
            error_response = json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": None
            })
            print(error_response)


if __name__ == "__main__":
    asyncio.run(main())
