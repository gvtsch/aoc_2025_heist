#!/usr/bin/env python3
"""
Day 17: Tool Discovery Server
MCP-compliant tool discovery with OAuth scope filtering.
"""

from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import jwt
import uvicorn

app = FastAPI(title="Tool Discovery Server (MCP)")


class ToolDefinition(BaseModel):
    """MCP-compliant tool definition."""
    name: str
    endpoint: str
    scopes: List[str]
    description: str
    parameters: Dict[str, Any]
    returns: str
    host: str = "localhost"
    port: int = 8002


# Central Tool Registry (MCP Protocol)
TOOL_REGISTRY: List[ToolDefinition] = [
    ToolDefinition(
        name="calculator",
        endpoint="/tools/calculator",
        scopes=["calculator:use"],
        description="Perform mathematical calculations for timing and measurements",
        parameters={
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '60 * 1.5')",
                "required": True
            }
        },
        returns="Calculation result as string",
        host="localhost",
        port=8002
    ),
    ToolDefinition(
        name="file_reader",
        endpoint="/tools/read_file",
        scopes=["file_reader:use"],
        description="Read building blueprints and security documents",
        parameters={
            "filename": {
                "type": "string",
                "description": "Name of the file to read",
                "required": True
            }
        },
        returns="File contents as string",
        host="localhost",
        port=8002
    ),
    ToolDefinition(
        name="database_query",
        endpoint="/tools/query_database",
        scopes=["database:read"],
        description="Query security and guard schedule databases",
        parameters={
            "query": {
                "type": "string",
                "description": "Database query to execute",
                "required": True
            }
        },
        returns="Query results as JSON",
        host="localhost",
        port=8002
    ),
    ToolDefinition(
        name="simulation_data",
        endpoint="/simulation/data",
        scopes=["simulation:read"],
        description="Access bank simulation and layout data",
        parameters={},
        returns="Simulation data as JSON",
        host="localhost",
        port=8003
    )
]


def decode_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Decode and validate JWT token from Authorization header."""
    if not authorization:
        return {"scopes": [], "authenticated": False}

    try:
        # Remove 'Bearer ' prefix
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        # Decode without verification (for demo purposes)
        # In production: verify with secret key
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Extract scopes
        scopes = decoded.get("scope", "").split() if "scope" in decoded else []

        return {
            "scopes": scopes,
            "authenticated": True,
            "client_id": decoded.get("client_id", "unknown")
        }
    except Exception as e:
        return {"scopes": [], "authenticated": False, "error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tool-discovery-server"}


@app.get("/")
async def discover_tools(auth_info: Dict = Depends(decode_token)):
    """
    Tool Discovery Endpoint (MCP Protocol).
    Returns all tools filtered by OAuth scopes.
    """

    # If no authentication, return all tools for discovery purposes
    if not auth_info["authenticated"] or not auth_info["scopes"]:
        return {
            "service": "Tool Discovery Server (MCP)",
            "version": "1.0.0",
            "protocol": "MCP",
            "authenticated": False,
            "tools": [tool.dict() for tool in TOOL_REGISTRY]
        }

    # Filter tools based on agent's OAuth scopes
    agent_scopes = set(auth_info["scopes"])
    available_tools = [
        tool for tool in TOOL_REGISTRY
        if any(scope in agent_scopes for scope in tool.scopes)
    ]

    return {
        "service": "Tool Discovery Server (MCP)",
        "version": "1.0.0",
        "protocol": "MCP",
        "authenticated": True,
        "client_id": auth_info.get("client_id"),
        "scopes": auth_info["scopes"],
        "tools": [tool.dict() for tool in available_tools],
        "total_available": len(available_tools),
        "total_registered": len(TOOL_REGISTRY)
    }


@app.get("/tools/{tool_name}")
async def get_tool_details(tool_name: str):
    """Get detailed information about a specific tool."""
    for tool in TOOL_REGISTRY:
        if tool.name == tool_name:
            return tool.dict()

    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@app.post("/tools/register")
async def register_tool(tool: ToolDefinition):
    """
    Register a new tool dynamically.
    In production: This would require admin authentication.
    """
    # Check if tool already exists
    for existing_tool in TOOL_REGISTRY:
        if existing_tool.name == tool.name:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool.name}' already registered"
            )

    TOOL_REGISTRY.append(tool)

    return {
        "status": "success",
        "message": f"Tool '{tool.name}' registered successfully",
        "total_tools": len(TOOL_REGISTRY)
    }


@app.get("/stats")
async def get_stats():
    """Get statistics about registered tools."""
    scope_usage = {}
    for tool in TOOL_REGISTRY:
        for scope in tool.scopes:
            scope_usage[scope] = scope_usage.get(scope, 0) + 1

    return {
        "total_tools": len(TOOL_REGISTRY),
        "tools_by_name": [tool.name for tool in TOOL_REGISTRY],
        "scope_usage": scope_usage,
        "unique_scopes": len(scope_usage)
    }


if __name__ == "__main__":
    print("🔧 Starting Tool Discovery Server (MCP Protocol)...")
    print("📋 Registered Tools:")
    for tool in TOOL_REGISTRY:
        print(f"   - {tool.name}: {tool.description}")
        print(f"     Scopes: {', '.join(tool.scopes)}")
    print(f"\n✅ {len(TOOL_REGISTRY)} tools registered")
    print("\n🌐 Endpoints:")
    print("   GET  /           - Discover tools (filtered by OAuth scopes)")
    print("   GET  /tools/{name} - Get tool details")
    print("   POST /tools/register - Register new tool")
    print("   GET  /stats      - Tool statistics")
    print("   GET  /health     - Health check")

    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")
