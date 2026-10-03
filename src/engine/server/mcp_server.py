"""MCP Server for ATS Framework - exposes test framework as tools for Claude and other MCP clients"""

import logging
import json
from typing import Any
import asyncio
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ToolResult,
)

logger = logging.getLogger("[mcp_server]")


class ATSMCPServer:
    """MCP Server wrapper for ATS Framework operations"""

    def __init__(self, framework):
        self.framework = framework
        self.server = Server("ats-framework")
        self._register_tools()

    def _register_tools(self):
        """Register all available MCP tools"""

        @self.server.call_tool()
        async def handle_tool_call(name: str, arguments: dict) -> ToolResult:
            """Route tool calls to appropriate handlers"""
            try:
                if name == "list_procedures":
                    return await self._tool_list_procedures()
                elif name == "get_procedure_info":
                    return await self._tool_get_procedure_info(arguments)
                elif name == "start_procedure":
                    return await self._tool_start_procedure(arguments)
                elif name == "stop_procedure":
                    return await self._tool_stop_procedure(arguments)
                elif name == "get_procedure_status":
                    return await self._tool_get_procedure_status(arguments)
                elif name == "get_framework_status":
                    return await self._tool_get_framework_status()
                elif name == "set_context_attribute":
                    return await self._tool_set_context_attribute(arguments)
                elif name == "get_context_attribute":
                    return await self._tool_get_context_attribute(arguments)
                else:
                    return ToolResult(
                        content=[TextContent(text=f"Unknown tool: {name}")],
                        is_error=True,
                    )
            except Exception as e:
                logger.error(f"Error handling tool {name}: {str(e)}")
                return ToolResult(
                    content=[TextContent(text=f"Error: {str(e)}")],
                    is_error=True,
                )

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Return list of available MCP tools"""
            return [
                Tool(
                    name="list_procedures",
                    description="List all procedures in the framework",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="get_procedure_info",
                    description="Get detailed information about a specific procedure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_label": {
                                "type": "string",
                                "description": "The label of the procedure",
                            }
                        },
                        "required": ["procedure_label"],
                    },
                ),
                Tool(
                    name="start_procedure",
                    description="Start a procedure by its label",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_label": {
                                "type": "string",
                                "description": "The label of the procedure to start",
                            }
                        },
                        "required": ["procedure_label"],
                    },
                ),
                Tool(
                    name="stop_procedure",
                    description="Stop a running procedure by its label",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_label": {
                                "type": "string",
                                "description": "The label of the procedure to stop",
                            }
                        },
                        "required": ["procedure_label"],
                    },
                ),
                Tool(
                    name="get_procedure_status",
                    description="Get the status of a procedure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "procedure_label": {
                                "type": "string",
                                "description": "The label of the procedure",
                            }
                        },
                        "required": ["procedure_label"],
                    },
                ),
                Tool(
                    name="get_framework_status",
                    description="Get overall framework status and statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="set_context_attribute",
                    description="Set an attribute in the framework context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The attribute key",
                            },
                            "value": {
                                "type": "string",
                                "description": "The attribute value (will be stored as string)",
                            },
                        },
                        "required": ["key", "value"],
                    },
                ),
                Tool(
                    name="get_context_attribute",
                    description="Get an attribute from the framework context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The attribute key",
                            }
                        },
                        "required": ["key"],
                    },
                ),
            ]

    async def _tool_list_procedures(self) -> ToolResult:
        """List all procedures"""
        procedures = []
        for idx, proc in enumerate(self.framework._procedure_list):
            procedures.append(
                {
                    "index": idx,
                    "label": proc.label,
                    "is_running": proc.is_running(),
                }
            )
        return ToolResult(
            content=[TextContent(text=json.dumps(procedures, indent=2))],
            is_error=False,
        )

    async def _tool_get_procedure_info(self, arguments: dict) -> ToolResult:
        """Get info about a specific procedure"""
        try:
            label = arguments["procedure_label"]
            procedure = self.framework.procedure_get_by_label(label)
            info = {
                "label": procedure.label,
                "is_running": procedure.is_running(),
                "current_step_index": procedure.get_active_step_index(),
                "total_steps": len(procedure.steps),
            }
            if procedure.get_active_step():
                info["current_step_label"] = procedure.get_active_step().label
            return ToolResult(
                content=[TextContent(text=json.dumps(info, indent=2))],
                is_error=False,
            )
        except KeyError:
            return ToolResult(
                content=[TextContent(text=f"Procedure '{label}' not found")],
                is_error=True,
            )

    async def _tool_start_procedure(self, arguments: dict) -> ToolResult:
        """Start a procedure"""
        try:
            label = arguments["procedure_label"]
            procedure = self.framework.procedure_get_by_label(label)
            procedure.start()
            return ToolResult(
                content=[
                    TextContent(
                        text=f"Procedure '{label}' started successfully"
                    )
                ],
                is_error=False,
            )
        except KeyError:
            return ToolResult(
                content=[TextContent(text=f"Procedure '{label}' not found")],
                is_error=True,
            )

    async def _tool_stop_procedure(self, arguments: dict) -> ToolResult:
        """Stop a procedure"""
        try:
            label = arguments["procedure_label"]
            procedure = self.framework.procedure_get_by_label(label)
            procedure.stop()
            return ToolResult(
                content=[TextContent(text=f"Procedure '{label}' stopped")],
                is_error=False,
            )
        except KeyError:
            return ToolResult(
                content=[TextContent(text=f"Procedure '{label}' not found")],
                is_error=True,
            )

    async def _tool_get_procedure_status(self, arguments: dict) -> ToolResult:
        """Get procedure status"""
        try:
            label = arguments["procedure_label"]
            procedure = self.framework.procedure_get_by_label(label)
            status = {
                "label": label,
                "is_running": procedure.is_running(),
                "state": procedure.state,
            }
            return ToolResult(
                content=[TextContent(text=json.dumps(status, indent=2))],
                is_error=False,
            )
        except KeyError:
            return ToolResult(
                content=[TextContent(text=f"Procedure '{label}' not found")],
                is_error=True,
            )

    async def _tool_get_framework_status(self) -> ToolResult:
        """Get framework status"""
        status = {
            "label": self.framework.get_label(),
            "procedure_count": len(self.framework._procedure_list),
            "running_procedures": sum(
                1
                for p in self.framework._procedure_list
                if p.is_running()
            ),
            "time_monotonic": self.framework.get_time_monotonic(),
            "time_datetime": str(self.framework.get_time_datetime()),
        }
        return ToolResult(
            content=[TextContent(text=json.dumps(status, indent=2))],
            is_error=False,
        )

    async def _tool_set_context_attribute(
        self, arguments: dict
    ) -> ToolResult:
        """Set context attribute"""
        try:
            key = arguments["key"]
            value = arguments["value"]
            self.framework.context.attribute_set(key, value)
            return ToolResult(
                content=[
                    TextContent(
                        text=f"Context attribute '{key}' set to '{value}'"
                    )
                ],
                is_error=False,
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(text=f"Error setting attribute: {str(e)}")],
                is_error=True,
            )

    async def _tool_get_context_attribute(
        self, arguments: dict
    ) -> ToolResult:
        """Get context attribute"""
        try:
            key = arguments["key"]
            value = self.framework.context.attribute_get(key)
            return ToolResult(
                content=[
                    TextContent(
                        text=f"Context attribute '{key}': {json.dumps(str(value))}"
                    )
                ],
                is_error=False,
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(text=f"Error getting attribute: {str(e)}")],
                is_error=True,
            )

    async def run(self, transport):
        """Start the MCP server"""
        async with self.server:
            await self.server.wait_shutdown()
