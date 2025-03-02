from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Model representing a single finding
class Finding(BaseModel):
    filename: str  
    line_range: str  
    description: str  

# Model representing the results
class GitLeaksResults(BaseModel):
    findings: List[Finding]
    scan_duration_ms: Optional[int] = None
    total_files_scanned: Optional[int] = None

# Model representing an error response
class ErrorResponse(BaseModel):
    exit_code: int  
    error_message: str  

# Model representing the response 
class GitLeaksResponse(BaseModel):
    findings: Optional[List[Finding]] = None  # Optional list of findings
    exit_code: Optional[int] = None  # Optional exit code
    error_message: Optional[str] = None  # Optional error message
    scan_summary: Optional[Dict[str, Any]] = None  # Scan statistics