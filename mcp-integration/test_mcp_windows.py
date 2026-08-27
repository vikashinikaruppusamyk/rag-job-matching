import asyncio
import json
import logging
from filesystem_mcp_server import FilesystemMCPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class WindowsCompatibleMCPTests:
    def __init__(self):
        self.server = None
        self.test_results = []

    async def setup(self):
        logger.info("Setting up MCP test environment...")
        self.server = FilesystemMCPServer(base_path="./test_data")
        logger.info("OK - MCP Server initialized")

    async def test_1_capabilities(self) -> bool:
        logger.info("\nTEST 1: Server Capabilities")
        try:
            request = json.dumps({"jsonrpc": "2.0", "method": "server/info", "params": {}, "id": 1})
            response_json = await self.server.handle_request(request)
            response = json.loads(response_json)
            if "error" in response and response["error"]:
                return False
            result = response.get("result", {})
            logger.info(f"OK - Server: {result['name']}")
            self.test_results.append(("Server Capabilities", True))
            return True
        except Exception as e:
            logger.error(f"FAILED: {str(e)}")
            self.test_results.append(("Server Capabilities", False))
            return False

    async def test_2_file_ops(self) -> bool:
        logger.info("\nTEST 2: File Operations")
        try:
            test_uri = "file://./test_data/test_file.txt"
            request = json.dumps({"jsonrpc": "2.0", "method": "resources/write", "params": {"uri": test_uri, "content": "Test", "overwrite": True}, "id": 3})
            response_json = await self.server.handle_request(request)
            response = json.loads(response_json)
            if "error" in response and response["error"]:
                return False
            logger.info("OK - File operations work")
            self.test_results.append(("File Operations", True))
            return True
        except Exception as e:
            self.test_results.append(("File Operations", False))
            return False

    async def test_3_resources(self) -> bool:
        logger.info("\nTEST 3: Resource Discovery")
        try:
            request = json.dumps({"jsonrpc": "2.0", "method": "resources/list", "params": {}, "id": 20})
            response_json = await self.server.handle_request(request)
            response = json.loads(response_json)
            if "error" in response and response["error"]:
                return False
            resources = response.get("result", [])
            logger.info(f"OK - Found {len(resources)} resources")
            self.test_results.append(("Resource Discovery", True))
            return True
        except Exception as e:
            self.test_results.append(("Resource Discovery", False))
            return False

    async def test_4_batch(self) -> bool:
        logger.info("\nTEST 4: Batch Processing")
        try:
            request = json.dumps({"jsonrpc": "2.0", "method": "batch/process", "params": {"operation": "extract_text", "files": ["file://./test_data/test.txt"], "options": {}}, "id": 40})
            response_json = await self.server.handle_request(request)
            response = json.loads(response_json)
            if "error" in response and response["error"]:
                return False
            logger.info("OK - Batch processing works")
            self.test_results.append(("Batch Processing", True))
            return True
        except Exception as e:
            self.test_results.append(("Batch Processing", False))
            return False

    async def test_5_watch(self) -> bool:
        logger.info("\nTEST 5: Directory Watching")
        try:
            request = json.dumps({"jsonrpc": "2.0", "method": "directory/watch", "params": {"uri": "file://./test_data", "pattern": "*.txt"}, "id": 60})
            response_json = await self.server.handle_request(request)
            response = json.loads(response_json)
            if "error" in response and response["error"]:
                return False
            logger.info("OK - Watch works")
            self.test_results.append(("Directory Watching", True))
            return True
        except Exception as e:
            self.test_results.append(("Directory Watching", False))
            return False

    async def test_6_errors(self) -> bool:
        logger.info("\nTEST 6: Error Handling")
        try:
            request = json.dumps({"jsonrpc": "2.0", "method": "invalid/method", "params": {}, "id": 80})
            response_json = await self.server.handle_request(request)
            response = json.loads(response_json)
            if "error" not in response or not response["error"]:
                return False
            logger.info("OK - Error handling works")
            self.test_results.append(("Error Handling", True))
            return True
        except Exception as e:
            self.test_results.append(("Error Handling", False))
            return False

    async def run_all(self):
        logger.info("\nMCP Integration Tests (Windows Compatible)")
        await self.setup()
        await self.test_1_capabilities()
        await self.test_2_file_ops()
        await self.test_3_resources()
        await self.test_4_batch()
        await self.test_5_watch()
        await self.test_6_errors()
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        logger.info("\n" + "="*60)
        for name, result in self.test_results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{status} - {name}")
        logger.info("="*60)
        logger.info(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
        
        if passed == total:
            logger.info("\nALL TESTS PASSED!")

async def main():
    tester = WindowsCompatibleMCPTests()
    await tester.run_all()

if __name__ == "__main__":
    asyncio.run(main())