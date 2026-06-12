# Dockerfile for AgentsFactory
# Build: docker build -t agentsfactory .
# Run: docker run -p 8501:8501 --env-file .env agentsfactory

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY setup/ ./setup/
COPY docs/ ./docs/
COPY .env.example .
COPY README.md .
COPY CLONE.md .

# Install Python dependencies
RUN uv venv .venv
RUN uv pip install streamlit plotly pandas requests

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start Command Center dashboard
CMD [".venv/bin/streamlit", "run", "src/agentkit/observability/command_center.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
