# Use multi-stage build to combine Gitleaks and Python
FROM zricethezav/gitleaks:latest AS gitleaks
FROM python:3.10-alpine3.16

# Install git
RUN apk add --no-cache git

# Copy gitleaks to our image
COPY --from=gitleaks /usr/bin/gitleaks /usr/bin/gitleaks

# Create workspace
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/* .

# Set the entrypoint to our Python script
ENTRYPOINT ["python", "/code/main.py"]