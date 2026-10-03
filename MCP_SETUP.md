# ATS Framework MCP Server Setup

This guide explains how to expose your ATS Framework as an MCP server so Claude and other MCP clients can control your tests.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI assistants like Claude to call tools and interact with external systems. By exposing your framework as an MCP server, Claude can:

- List available test procedures
- Start and stop tests
- Query test status
- Manage framework context
- Get real-time framework statistics

## Installation

1. Install the MCP SDK (already added to requirements.txt):
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install mcp==0.8.1
```

## Starting the MCP Server

### Option 1: Command Line

Run the MCP server launcher directly:

```bash
python mcp_server_launcher.py
```

The server will start on stdio transport and wait for MCP clients to connect.

### Option 2: From Claude Code CLI

Configure Claude Code to start the MCP server automatically.

Edit your Claude Code config file:
- **Linux/Mac**: `~/.claude/settings.json`
- **Windows**: `%USERPROFILE%\.claude\settings.json`

Add the MCP server configuration:

```json
{
  "mcpServers": {
    "ats-framework": {
      "command": "python",
      "args": [
        "C:\\path\\to\\ats_python\\mcp_server_launcher.py"
      ],
      "disabled": false
    }
  }
}
```

Replace `C:\\path\\to\\ats_python` with your actual project path.

## Available Tools

Once the MCP server is running, Claude can access the following tools:

### list_procedures
Lists all procedures in the framework with their running status.

Example Claude request:
```
"Show me all available test procedures"
```

### get_procedure_info
Get detailed information about a specific procedure.

Parameters:
- `procedure_label` (string): The label of the procedure

### start_procedure
Start a procedure by its label.

Parameters:
- `procedure_label` (string): The label of the procedure to start

Example Claude request:
```
"Start the 'base_project_alfa' procedure"
```

### stop_procedure
Stop a running procedure.

Parameters:
- `procedure_label` (string): The label of the procedure to stop

### get_procedure_status
Get the current status of a procedure.

Parameters:
- `procedure_label` (string): The label of the procedure

### get_framework_status
Get overall framework statistics:
- Total procedure count
- Number of running procedures
- Current time
- Framework version

### set_context_attribute
Set an attribute in the framework context.

Parameters:
- `key` (string): Attribute name
- `value` (string): Attribute value

### get_context_attribute
Retrieve an attribute from the framework context.

Parameters:
- `key` (string): Attribute name

## Testing the MCP Server

### Test with Claude Code

Once configured in `settings.json`, Claude Code will automatically load the MCP server. You can test it by:

1. Opening Claude Code
2. Asking: "What procedures are available in my framework?"
3. Claude should use the `list_procedures` tool to respond

### Manual Testing (Optional)

You can test the server manually by running it in a terminal and connecting with an MCP client.

## Troubleshooting

### Server doesn't start

1. Verify the Python path is correct in `settings.json`
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Ensure the framework initializes correctly by running `python src/main.py` first

### Tools not appearing in Claude

1. Check that `mcpServers` is properly configured in `settings.json`
2. Restart Claude Code after modifying settings
3. Check the MCP server logs in Claude Code's debug output

### Connection issues

The MCP server uses stdin/stdout for communication. Make sure:
- The launcher script has execute permissions
- Python is in your system PATH
- No other process is interfering with stdio

## Adding More Tools

To extend the MCP server with additional tools:

1. Edit [src/engine/server/mcp_server.py](src/engine/server/mcp_server.py)
2. Add a new tool handler method (e.g., `_tool_my_feature()`)
3. Register it in the `list_tools()` method
4. Add the route in `handle_tool_call()`

Example:

```python
async def _tool_my_feature(self, arguments: dict) -> ToolResult:
    """My new feature"""
    result = self.framework.my_operation(arguments["param"])
    return ToolResult(
        content=[TextContent(text=json.dumps(result))],
        is_error=False,
    )
```

Then register in `list_tools()`:

```python
Tool(
    name="my_feature",
    description="Description of my feature",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"],
    },
)
```

## Next Steps

1. **Customize Tools**: Add more tools specific to your testing workflow
2. **Add Authentication**: If needed, add security measures for MCP access
3. **Monitor Performance**: Track MCP calls to ensure smooth test execution
4. **Expand Context**: Add more framework state to context for complex workflows

