import json
import subprocess
import sys
import time
import os
from typing import Union
from models import Finding, GitLeaksResults, ErrorResponse, GitLeaksResponse

def run_gitleaks(args: list[str]) -> tuple[int, str]:
    try:
        # Set default arguments if none provided
        if not args:
            args = ["directory", "/code/repo", "--report-path", "/code/repo/output.json"]
            
        print(f"Running command: gitleaks {' '.join(args)}", file=sys.stderr)

        result = subprocess.run(
            ["gitleaks"] + args,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Handle exit codes according to gitleaks docs
        if result.returncode == 0:  # no leaks present
            return 0, result.stdout or result.stderr
        elif result.returncode == 1:  # leaks or error encountered
            if "leaks found:" in (result.stdout or result.stderr):
                # This is actually a success case where leaks were found
                return 0, result.stdout or result.stderr
            else:
                # This is an error case
                return 2, f"Gitleaks scan failed: {result.stderr}"
        elif result.returncode == 126:  # unknown flag
            return 2, f"Gitleaks scan failed: unknown argument '{args[-1]}'"
        else:
            return 2, f"Gitleaks scan failed: {result.stderr}"
        
    except Exception as e:
        return 2, f"Failed to run gitleaks: {str(e)}"

def count_unique_files(scan_path):
    """Count files in directory using a simple file system walk"""
    if not os.path.exists(scan_path):
        return 0
        
    if os.path.isfile(scan_path):
        return 1
        
    file_count = 0
    for root, _, files in os.walk(scan_path):
        # Skip .git directory
        if ".git" in root.split(os.sep):
            continue
        file_count += len(files)
    
    return file_count

def process_gitleaks_output(json_file_path: str, scan_path: str = "/code/repo") -> Union[GitLeaksResults, ErrorResponse]:
    try:
        # Open the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            
        findings = []
        
        # Handle both list and dictionary formats from Gitleaks
        if isinstance(data, dict):
            data = data.get('findings', [])
        
        # Process each finding (lower and upper)
        for finding in data:
            findings.append(Finding(
                filename=finding.get('file', finding.get('File', '')),
                line_range=f"{finding.get('startLine', finding.get('StartLine', ''))}-{finding.get('endLine', finding.get('EndLine', ''))}",
                description=finding.get('description', finding.get('Description', 'Potential secret found'))
            ))
        
        # Count unique filenames in findings
        unique_files = set()
        for finding in findings:
            unique_files.add(finding.filename)
        
        # Get file count from the filesystem
        total_files = count_unique_files(scan_path)
        
        result = GitLeaksResults(findings=findings)
        result.total_files_scanned = total_files
        return result
            
    except Exception as e:
        return ErrorResponse(
            exit_code=2,
            error_message=f"Failed to process gitleaks output: {str(e)}"
        )
    
def main():
    start_time = time.time()

    # Create response object
    response = GitLeaksResponse()
    
    print("Starting Gitleaks scan...", file=sys.stderr)
    
    # Determine scan path from arguments
    scan_path = "/code/repo"
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "directory" and i+1 < len(sys.argv[1:]):
            scan_path = sys.argv[i+2]
    
    # Run gitleaks without the first argument (script name)
    exit_code, output = run_gitleaks(sys.argv[1:])
    
    # Handle the various exit codes and output processing
    if exit_code == 126:
       error_response = ErrorResponse(
            exit_code=exit_code,
            error_message=output
        )
       response.exit_code = error_response.exit_code
       response.error_message = error_response.error_message
    elif exit_code != 0:
        error_response = ErrorResponse(
            exit_code=exit_code,
            error_message=f"Gitleaks scan failed: {output}"
        )
        response.exit_code = error_response.exit_code
        response.error_message = error_response.error_message
    else:
        # Process successful output (including when leaks were found)
        result = process_gitleaks_output("/code/repo/output.json", scan_path)
        
        if isinstance(result, ErrorResponse):
            # Handle processing error
            response.exit_code = result.exit_code
            response.error_message = result.error_message
        else:
            # Handle success case
            response.findings = result.findings
            response.scan_summary = {
                "duration_ms": int((time.time() - start_time) * 1000),
                "total_files_scanned": result.total_files_scanned,
                "files_with_secrets": len(set(f.filename for f in result.findings)) if result.findings else 0
            }
    
    # Print the results to stderr for user feedback
    if not response.findings:
        print("No secrets were found in the scanned files.", file=sys.stderr)
    elif response.error_message:
        print(f"Error occurred: {response.error_message}", file=sys.stderr)
    else:
        unique_files_with_secrets = len(set(f.filename for f in response.findings))
        print(
            f"Found {len(response.findings)} potential secrets in {unique_files_with_secrets} files.", 
            file=sys.stderr
        )
        print(
            f"Scan completed in {response.scan_summary.get('duration_ms', 0)/1000:.2f} seconds.", 
            file=sys.stderr
        )
    
    # Convert the response to JSON and print to stdout
    json_output = response.model_dump_json(exclude_none=True, indent=2)
    print(json_output)
    
    # Exit with appropriate code
    sys.exit(response.exit_code if response.exit_code is not None else 0)

if __name__ == "__main__":
    main()