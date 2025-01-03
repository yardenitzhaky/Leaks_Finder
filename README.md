# 🔐 Gitleaks Python Wrapper

This mini-project provides a Docker-based wrapper around the Gitleaks secret detection tool, integrating it with Python to provide structured output. It scans repositories or directories for potential secrets and presents the findings in a standardized JSON format.

## ✨ Features

-  Combines Gitleaks secret detection with Python processing
-  Provides structured JSON output using Pydantic models
-  Supports flexible command-line arguments
- ⚠ Includes comprehensive error handling
- 🛠 Uses Docker for consistent environment and easy deployment

## 📖 Prerequisites

-  Docker installed on your system
-  Git (for repository scanning)

## 📥 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yardenitzhaky/Leaks_Finder
   cd Leaks_Finder
   ```

2. Make the run script executable:
   ```bash
   chmod +x run.sh
   ```

##  Usage

The wrapper can be run using the provided `run.sh` script, which handles building and running the Docker container.
For example usage, enter the testing directory and run:

```bash
cd fake-public-secrets
../run.sh directory .
```

###  Output Format

The tool outputs JSON in the following format for successful scans:

```json
{
  "findings": [
    {
      "filename": "example.tf",
      "line_range": "11-11",
      "description": "Identified a pattern that may indicate AWS ..."
    }
  ]
}
```

For errors, the output will be:

```json
{
  "exit_code": 2,
  "error_message": "Gitleaks scan failed: [error details]"
}
```

## ❗ Error Codes

-  **0**: Success (no leaks found or scan completed with findings)
-  **2**: Error (scan failed or invalid arguments)
-  **126**: Unknown command flag

## 💡 Notes

- The wrapper uses **Gitleaks version 8.19.0** or later, which has updated command syntax.
- All paths in the container are relative to `/code/repo/`.
- The current working directory is mounted at `/code/repo/` in the container.

