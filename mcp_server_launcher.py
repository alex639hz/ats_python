"""Launch the ATS Framework as an MCP server for Claude and other MCP clients"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from engine.framework import framework
from engine.server.mcp_server import ATSMCPServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("[mcp_launcher]")


async def main():
    """Start the MCP server"""
    logger.info("Starting ATS Framework MCP Server...")

    try:
        from mcp.server.stdio import stdio_server

        mcp_server = ATSMCPServer(framework)
        logger.info("MCP Server initialized with framework")
        logger.info("Available tools:")
        for tool_name in [
            "list_procedures",
            "get_procedure_info",
            "start_procedure",
            "stop_procedure",
            "get_procedure_status",
            "get_framework_status",
            "set_context_attribute",
            "get_context_attribute",
        ]:
            logger.info(f"  - {tool_name}")

        async with stdio_server(mcp_server.server) as (read_stream, write_stream):
            logger.info("MCP Server running on stdio transport - ready for connections")
            await mcp_server.server.wait_shutdown()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP Server shutting down...")
        sys.exit(0)
