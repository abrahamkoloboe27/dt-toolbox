FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY examples/ ./examples/

# Install package
RUN pip install --no-cache-dir -e .

# Default command - run success example
CMD ["python", "examples/example_success.py"]
