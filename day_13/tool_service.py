"""
Tool Service - OAuth-Protected Agent Tools
Alle Agent Tools werden zu geschützten Microservices mit OAuth
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional
import jwt
import json
import uvicorn

app = FastAPI(
    title="Agent Tool Service",
    description="OAuth-protected tools for specialized agent capabilities",
    version="1.0.0"
)

security = HTTPBearer()

# JWT Secret (in real app: environment variable)
JWT_SECRET = "heist-tools-secret-key"
JWT_ALGORITHM = "HS256"

# Tool permissions mapping
TOOL_PERMISSIONS = {
    "safecracker": ["calculator:use"],
    "hacker": ["file_reader:use"],
    "mole": ["database_query:use"],
    "planner": []  # No direct tool access
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
        agent = payload.get("agent")
        scopes = payload.get("scopes", [])
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing agent"
            )
        
        return {"agent": agent, "scopes": scopes}
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def require_scope(required_scope: str):
    """Decorator to require specific OAuth scope"""
    def scope_checker(auth_info: dict = Depends(validate_token)):
        if required_scope not in auth_info["scopes"]:
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
    auth_info: dict = Depends(require_scope("calculator:use"))
):
    """OAuth-protected calculator for safe timing calculations"""
    try:
        # Basic safety check
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in request.expression):
            raise ValueError("Only basic math operations allowed")
        
        result = eval(request.expression)
        
        return ToolResponse(
            success=True,
            result=f"Calculation: {request.expression} = {result}",
            tool_used="calculator",
            agent=auth_info["agent"]
        )
    
    except Exception as e:
        return ToolResponse(
            success=False,
            error=f"Calculation error: {str(e)}",
            tool_used="calculator", 
            agent=auth_info["agent"]
        )

@app.post("/tools/file_reader", response_model=ToolResponse)
def file_reader_tool(
    request: FileReadRequest,
    auth_info: dict = Depends(require_scope("file_reader:use"))
):
    """OAuth-protected file reader for technical documents"""
    
    # Simulated file system
    files = {
        "bank_layout.txt": """
BANK LAYOUT - CONFIDENTIAL
Main Vault: Steel-reinforced door, 3-hour time lock
Security Office: Second floor, overlooking main floor
Elevator: Service elevator connects all floors
Emergency Exit: Fire stairs, alarmed but bypassable
Safe Deposit Room: Adjacent to main vault, separate lock system
        """.strip(),
        
        "security_system.txt": """
SECURITY SPECIFICATIONS
Motion Sensors: Zones A-F, 30-second delay on activation
Cameras: 16 cameras, 72-hour local storage
Backup Power: 4-hour battery backup for all systems
Access Cards: RFID system, logs all entries
Panic Button: Silent alarm to central monitoring
        """.strip(),
        
        "timing_specs.txt": """
TIME LOCK SPECIFICATIONS  
Manufacturer: TimeGuard Pro X500
Lock Duration: 3 hours minimum
Override: Requires two manager keys
Backup: Manual mechanical lock
Vulnerability: Electromagnetic interference causes 10-minute reset
        """.strip()
    }
    
    try:
        if request.filename in files:
            result = files[request.filename]
        else:
            available = ", ".join(files.keys())
            result = f"File '{request.filename}' not found. Available files: {available}"
        
        return ToolResponse(
            success=True,
            result=result,
            tool_used="file_reader",
            agent=auth_info["agent"]
        )
    
    except Exception as e:
        return ToolResponse(
            success=False,
            error=f"File read error: {str(e)}",
            tool_used="file_reader",
            agent=auth_info["agent"]
        )

@app.post("/tools/database_query", response_model=ToolResponse)
def database_query_tool(
    request: DatabaseQueryRequest,
    auth_info: dict = Depends(require_scope("database_query:use"))
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
            else:
                result = """
GUARD SCHEDULE - TODAY
08:00-16:00: Miller, Johnson (Main Floor)
16:00-00:00: Rodriguez, Kim (Main Floor) 
00:00-08:00: Chen, Williams (Night Shift)
Security Office: Supervisor Anderson (08:00-17:00)
                """.strip()
        
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
        
        elif "access_level" in query:
            result = """
ACCESS LEVELS
Level 1: Public areas only
Level 2: Security checkpoints
Level 3: Restricted areas, safe deposit access
Level 4: Vault area, security systems
Level 5: Master access, all systems
            """.strip()
        
        else:
            result = f"No data found for query: {request.query}"
        
        return ToolResponse(
            success=True,
            result=result,
            tool_used="database_query",
            agent=auth_info["agent"]
        )
    
    except Exception as e:
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
        "calculator:use": {
            "name": "calculator",
            "description": "Mathematical calculations for timing and logistics",
            "endpoint": "/tools/calculator"
        },
        "file_reader:use": {
            "name": "file_reader", 
            "description": "Access to technical documents and blueprints",
            "endpoint": "/tools/file_reader"
        },
        "database_query:use": {
            "name": "database_query",
            "description": "Query security databases for intel",
            "endpoint": "/tools/database_query"
        }
    }
    
    for scope in scopes:
        if scope in tool_descriptions:
            available_tools.append(tool_descriptions[scope])
    
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
    print("🛠️ Starting Agent Tool Service (OAuth Protected)")
    print("📊 Tools: Calculator, File Reader, Database Query")
    print("🔐 OAuth scopes required for tool access")
    print("🚀 Service running on http://localhost:8003")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)