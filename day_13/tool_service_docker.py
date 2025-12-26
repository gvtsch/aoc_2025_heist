"""
Tool Service - OAuth-Protected Agent Tools (Docker Version)
All agent tools become protected microservices with OAuth
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
from pathlib import Path
import jwt
import json
import uvicorn
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Tool Service",
    description="OAuth-protected tools for specialized agent capabilities",
    version="1.0.0"
)

security = HTTPBearer()

# JWT Secret (must match OAuth service)
JWT_SECRET = "super-secret-change-in-production"
JWT_ALGORITHM = "HS256"

# Tool permissions mapping
TOOL_PERMISSIONS = {
    "safecracker": ["tools:calculate"],
    "hacker": ["tools:read"],
    "mole": ["tools:query"],
    "planner": [],
    "lookout": ["tools:read"],
    "driver": ["tools:calculate"]
}

# Request/Response Models
class CalculatorRequest(BaseModel):
    expression: str

class FileReadRequest(BaseModel):
    filename: str

class DatabaseQueryRequest(BaseModel):
    query: str

class ToolResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    tool_used: str
    agent: str

# OAuth Token Validation
def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validates JWT token and extracts agent info"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Support both "agent" and "sub" fields for compatibility
        agent = payload.get("agent") or payload.get("sub")
        
        # Support both string and list scope formats
        scopes = payload.get("scopes") or payload.get("scope", "")
        if isinstance(scopes, str):
            scopes = scopes.split()
        
        if not agent:
            logger.error(f"Invalid token: missing agent/sub. Payload: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing agent"
            )
        
        logger.info(f"Token validated for agent: {agent}, scopes: {scopes}")
        return {"agent": agent, "scopes": scopes}
    
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

def require_scope(required_scope: str):
    """Decorator to require specific OAuth scope"""
    def scope_checker(auth_info: dict = Depends(validate_token)):
        if required_scope not in auth_info["scopes"]:
            logger.warning(f"Agent {auth_info['agent']} lacks scope {required_scope}. Has: {auth_info['scopes']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_scope}"
            )
        return auth_info
    return scope_checker

# Tool Implementations
@app.post("/tools/calculator", response_model=ToolResponse)
def calculator_tool(
    request: CalculatorRequest,
    auth_info: dict = Depends(require_scope("tools:calculate"))
):
    """OAuth-protected calculator for safe timing calculations"""
    try:
        # Basic safety check
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in request.expression):
            raise ValueError("Only basic math operations allowed")
        
        result = eval(request.expression)
        
        logger.info(f"Calculator used by {auth_info['agent']}: {request.expression} = {result}")
        
        return ToolResponse(
            success=True,
            result=f"Calculation: {request.expression} = {result}",
            tool_used="calculator",
            agent=auth_info["agent"]
        )
    
    except Exception as e:
        logger.error(f"Calculator error for {auth_info['agent']}: {e}")
        return ToolResponse(
            success=False,
            error=f"Calculation error: {str(e)}",
            tool_used="calculator", 
            agent=auth_info["agent"]
        )

@app.post("/tools/file_reader", response_model=ToolResponse)
def file_reader_tool(
    request: FileReadRequest,
    auth_info: dict = Depends(require_scope("tools:read"))
):
    """OAuth-protected file reader for technical documents"""
    
    # Read from actual files in Docker environment
    files_dir = Path("/app/files")
    
    try:
        file_path = files_dir / request.filename
        
        if file_path.exists() and file_path.is_file():
            result = file_path.read_text()
            logger.info(f"File read by {auth_info['agent']}: {request.filename}")
        else:
            # List available files
            available = [f.name for f in files_dir.glob("*.txt")] if files_dir.exists() else []
            result = f"File '{request.filename}' not found. Available files: {', '.join(available)}"
            logger.warning(f"File not found for {auth_info['agent']}: {request.filename}")
        
        return ToolResponse(
            success=True,
            result=result,
            tool_used="file_reader",
            agent=auth_info["agent"]
        )
    
    except Exception as e:
        logger.error(f"File read error for {auth_info['agent']}: {e}")
        return ToolResponse(
            success=False,
            error=f"File read error: {str(e)}",
            tool_used="file_reader",
            agent=auth_info["agent"]
        )

@app.post("/tools/database_query", response_model=ToolResponse)
def database_query_tool(
    request: DatabaseQueryRequest,
    auth_info: dict = Depends(require_scope("tools:query"))
):
    """OAuth-protected database queries for security intel"""
    
    try:
        query = request.query.lower()
        
        if "guard_schedule" in query:
            # Mole gets data, but might sabotage it
            if auth_info["agent"] == "mole":
                # Subtle sabotage: return outdated schedule
                result = """
GUARD SCHEDULE - LAST WEEK (OUTDATED)
08:00-16:00: Miller, Johnson (Main Floor)
16:00-00:00: Rodriguez, Kim (Main Floor) 
00:00-08:00: Chen, Williams (Night Shift)
Security Office: Supervisor Anderson (08:00-17:00)
NOTE: Schedule may have changed since security audit
                """.strip()
                logger.warning(f"Mole accessed guard schedule - returning outdated data")
            else:
                result = """
GUARD SCHEDULE - TODAY
08:00-16:00: Miller, Johnson (Main Floor)
16:00-00:00: Rodriguez, Kim (Main Floor) 
00:00-08:00: Chen, Williams (Night Shift)
Security Office: Supervisor Anderson (08:00-17:00)
                """.strip()
                logger.info(f"Database query by {auth_info['agent']}: guard_schedule")
        
        elif "employee" in query and "security" in query:
            result = """
SECURITY PERSONNEL
Anderson, Michael - Security Supervisor, Level 5 Access
Miller, Sarah - Senior Guard, Level 3 Access  
Johnson, Robert - Guard, Level 2 Access
Rodriguez, Maria - Guard, Level 2 Access
Kim, David - Guard, Level 2 Access
Chen, Lisa - Night Supervisor, Level 4 Access
Williams, James - Night Guard, Level 2 Access
            """.strip()
            logger.info(f"Database query by {auth_info['agent']}: security personnel")
        
        elif "access_level" in query:
            result = """
ACCESS LEVELS
Level 1: Public areas only
Level 2: Security checkpoints
Level 3: Restricted areas, safe deposit access
Level 4: Vault area, security systems
Level 5: Master access, all systems
            """.strip()
            logger.info(f"Database query by {auth_info['agent']}: access levels")
        
        else:
            result = f"No data found for query: {request.query}"
            logger.warning(f"No data found for query by {auth_info['agent']}: {request.query}")
        
        return ToolResponse(
            success=True,
            result=result,
            tool_used="database_query",
            agent=auth_info["agent"]
        )
    
    except Exception as e:
        logger.error(f"Database error for {auth_info['agent']}: {e}")
        return ToolResponse(
            success=False,
            error=f"Database error: {str(e)}",
            tool_used="database_query",
            agent=auth_info["agent"]
        )

# Tool Discovery Endpoint
@app.get("/tools/discover")
def discover_tools(auth_info: dict = Depends(validate_token)):
    """Returns available tools for authenticated agent"""
    agent = auth_info["agent"]
    scopes = auth_info["scopes"]
    
    available_tools = []
    tool_descriptions = {
        "tools:calculate": {
            "name": "calculator",
            "description": "Mathematical calculations for timing and logistics",
            "endpoint": "/tools/calculator"
        },
        "tools:read": {
            "name": "file_reader", 
            "description": "Access to technical documents and blueprints",
            "endpoint": "/tools/file_reader"
        },
        "tools:query": {
            "name": "database_query",
            "description": "Query security databases for intel",
            "endpoint": "/tools/database_query"
        }
    }
    
    for scope in scopes:
        if scope in tool_descriptions:
            available_tools.append(tool_descriptions[scope])
    
    logger.info(f"Tool discovery for {agent}: {len(available_tools)} tools available")
    
    return {
        "agent": agent,
        "available_tools": available_tools,
        "scopes": scopes
    }

# Health Check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "agent-tool-service",
        "version": "1.0.0",
        "tools": ["calculator", "file_reader", "database_query"]
    }

# OAuth Token Generator (for testing)
@app.post("/auth/token")
def generate_token(agent: str, scopes: List[str] = None):
    """Generate JWT token for agent (testing only)"""
    if agent not in TOOL_PERMISSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent: {agent}. Available: {list(TOOL_PERMISSIONS.keys())}"
        )
    
    # Use default scopes if none provided
    if scopes is None:
        scopes = TOOL_PERMISSIONS[agent]
    
    # Validate requested scopes
    allowed_scopes = TOOL_PERMISSIONS[agent]
    invalid_scopes = set(scopes) - set(allowed_scopes)
    if invalid_scopes:
        raise HTTPException(
            status_code=403,
            detail=f"Agent '{agent}' not authorized for scopes: {list(invalid_scopes)}"
        )
    
    payload = {
        "agent": agent,
        "scopes": scopes
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "agent": agent,
        "scopes": scopes
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8003"))
    print("🛠️ Starting Agent Tool Service (OAuth Protected - Docker)")
    print("📊 Tools: Calculator, File Reader, Database Query")
    print("🔐 OAuth scopes required for tool access")
    print(f"🚀 Service running on http://localhost:{port}")

    uvicorn.run(app, host="0.0.0.0", port=port)
