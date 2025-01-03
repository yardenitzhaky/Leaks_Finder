import json
import subprocess
import sys
from typing import Union

from models import Finding, GitLeaksResponse

def run_gitleaks(args: list[str]) -> tuple[int, str]:
    try:
        # Set default arguments if none provided
        if not args:
            args = ["directory", "/code/repo", "--report-path", "/code/repo/output.json"]

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

def process_gitleaks_output(json_file_path: str) -> Union[list[Finding], tuple[int, str]]:
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
            
        return findings
            
    except Exception as e:
        return 2, f"Failed to process gitleaks output: {str(e)}"
    
def main():
    # Create response object
    response = GitLeaksResponse()
    
    print("Starting Gitleaks scan...", file=sys.stderr)
    
    # Run gitleaks without the first argument (script name)
    exit_code, output = run_gitleaks(sys.argv[1:])
    
    # Handle the various exit codes and output processing
    if exit_code == 126:
        response.exit_code = exit_code
        response.error_message = output
    elif exit_code != 0:
        response.exit_code = exit_code
        response.error_message = f"Gitleaks scan failed: {output}"
    else:
        # Process successful output (including when leaks were found)
        result = process_gitleaks_output("/code/repo/output.json")
        
        if isinstance(result, tuple):
            # Handle processing error
            response.exit_code, response.error_message = result
        else:
            # Handle success case
            response.findings = result
    
    # Print the formatted output
    result = response.model_dump_json(exclude_none=True, indent=2)
    if response.findings == []:
        print("No secrets were found in the scanned files.", file=sys.stderr)
    elif response.error_message:
        print(f"Error occurred: {response.error_message}", file=sys.stderr)
    else:
        print(f"Found {len(response.findings)} potential secrets.", file=sys.stderr)
    
    print(result)
    
    # Exit with appropriate code
    sys.exit(response.exit_code if response.exit_code is not None else 0)

if __name__ == "__main__":
    main()