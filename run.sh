#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Build the image from the correct directory with no cache to ensure fresh build
docker build --no-cache -t gitleaks-python "$SCRIPT_DIR"

# Run the container with the current directory mounted, this is diffrent from the example because in v8.19.0 they changed the syntax
docker run -v "$(pwd):/code/repo" --workdir /code/repo gitleaks-python "$@"