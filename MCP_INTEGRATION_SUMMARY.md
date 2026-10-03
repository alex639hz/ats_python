# MCP Server Integration Summary

## What Was Added

Your ATS Framework has been integrated as an MCP (Model Context Protocol) server. This allows Claude and other MCP clients to control your test framework remotely.

### New Files

1. **`src/engine/server/mcp_server.py`** — Core MCP server implementation
   - Wraps framework operations as MCP tools
   - Handles tool registration and execution
   - Provides 8 tools for framework control

2. **`mcp_server_launcher.py`** — Entry point for the MCP server
   - Initializes the framework and MCP server
   - Sets up stdio transport for Claude connections
   - Includes error handling and logging

3. **`MCP_SETUP.md`** — Complete setup and usage guide
   - Detailed installation instructions
   - Configuration examples
   - Tool descriptions
   - Troubleshooting guide

4. **`.claude-settings-example.json`** — Configuration template
   - Copy this to your Claude Code settings.json
   - Update the path to your ats_python directory

5. **`requirements.txt`** — Updated with mcp SDK dependency
   - Added `mcp==0.8.1`

## Available Tools (from Claude)

Claude can now use these tools to control your framework:

| Tool | Purpose |
|------|---------|
| `list_procedures` | See all available test procedures |
| `get_procedure_info` | Get details about a specific procedure |
| `start_procedure` | Start a test procedure |
| `stop_procedure` | Stop a running procedure |
| `get_procedure_status` | Check current procedure status |
| `get_framework_status` | Get overall framework statistics |
| `set_context_attribute` | Set framework context values |
| `get_context_attribute` | Get framework context values |

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the MCP Server (Manual)
```bash
python mcp_server_launcher.py
```

You should see:
```
Starting ATS Framework MCP Server...
MCP Server initialized with framework
Available tools:
  - list_procedures
  - get_procedure_info
  - ... (more tools)
MCP Server running on stdio transport - ready for connections
```

### 3. Configure Claude Code
- Copy `.claude-settings-example.json` to your Claude Code settings location
- On Windows: `%USERPROFILE%\.claude\settings.json`
- On Mac/Linux: `~/.claude/settings.json`
- Update the path to your ats_python directory
- Restart Claude Code

### 4. Test with Claude
Open Claude Code and ask:
```
"What procedures are available in my test framework?"
```

Claude should respond using the `list_procedures` tool.

## Integration Points

### Framework
The MCP server directly accesses:
- `framework._procedure_list` — List of all procedures
- `framework._procedure_dict` — Procedure lookup by label
- `framework.context` — Shared context attributes
- Procedure methods: `start()`, `stop()`, `is_running()`, etc.

### Server Architecture
```
Claude Code (MCP Client)
    ↓ stdio
MCP Server (mcp_server_launcher.py)
    ↓
ATSMCPServer (src/engine/server/mcp_server.py)
    ↓
Framework (src/engine/framework.py)
    ↓
Procedures, Pipelines, Instruments
```

## Next Steps

### Short Term
1. Test the MCP connection with simple queries
2. Run a procedure through Claude using `start_procedure`
3. Monitor procedure status with `get_procedure_status`

### Medium Term
1. Add more specialized tools (e.g., `run_test_suite`, `get_test_results`)
2. Integrate with your database for historical test data
3. Add authentication/authorization if needed

### Long Term
1. Create custom tools for your specific test workflows
2. Add machine learning for test result analysis
3. Build dashboards or reports through Claude

## Example Claude Interactions

### List all procedures
**You:** "Show me all available test procedures"
**Claude:** Uses `list_procedures` tool → Shows available tests

### Start a test
**You:** "Start the base_project_alfa procedure"
**Claude:** Uses `start_procedure` with procedure_label="base_project_alfa"

### Check status
**You:** "What's the status of the thermal test?"
**Claude:** Uses `get_procedure_status` → Reports running/stopped status

### Get framework info
**You:** "How many tests are running right now?"
**Claude:** Uses `get_framework_status` → Reports running procedure count

## Extending the MCP Server

To add more tools to expose more framework functionality:

1. Add a tool handler method in `src/engine/server/mcp_server.py`:
```python
async def _tool_my_feature(self, arguments: dict) -> ToolResult:
    # Implement your feature
    result = self.framework.my_operation(...)
    return ToolResult(
        content=[TextContent(text=json.dumps(result))],
        is_error=False,
    )
```

2. Register it in the `list_tools()` method:
```python
Tool(
    name="my_feature",
    description="Description of what this does",
    inputSchema={...}
)
```

3. Add routing in `handle_tool_call()`:
```python
elif name == "my_feature":
    return await self._tool_my_feature(arguments)
```

## Troubleshooting

### MCP Server won't start
- Check Python path in settings.json
- Run `pip install -r requirements.txt` again
- Check for error messages in the terminal

### Claude doesn't see the tools
- Restart Claude Code after updating settings.json
- Verify the command and args in settings.json are correct
- Check that the mcp_server_launcher.py path is absolute, not relative

### Procedures not responding to Claude commands
- Verify procedures are actually in `framework._procedure_list`
- Check procedure labels match exactly (case-sensitive)
- Monitor the launcher output for error messages

## Files Reference

- [src/engine/server/mcp_server.py](src/engine/server/mcp_server.py) — MCP server logic
- [mcp_server_launcher.py](mcp_server_launcher.py) — Launch script
- [MCP_SETUP.md](MCP_SETUP.md) — Detailed setup guide
- [.claude-settings-example.json](.claude-settings-example.json) — Config template

