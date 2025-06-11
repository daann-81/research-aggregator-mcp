FROM python:3.12-slim

# Define build argument with default value (production)
ARG INSTALL_DEV=false

### Set environment variables ###

# Ensures Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Disables pip cache to reduce image size
ENV PIP_NO_CACHE_DIR=1
# Stops pip from checking for updates
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install curl (needed for Poetry installer)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# Install git for development
RUN if [ "$INSTALL_DEV" = "true" ] ; then apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* ; fi

### install poetry ###

# Install Poetry using official installer
RUN curl -sSL https://install.python-poetry.org | python3 -
# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"
# Configure Poetry: don't create virtual environment (we're already in a container)
RUN poetry config virtualenvs.create false

# Set working directory
WORKDIR /app

# Copy Poetry configuration files
COPY README.md pyproject.toml poetry.lock* ./

# Install dependencies based on build argument
RUN echo "INSTALL_DEV is set to: $INSTALL_DEV" && \
    if [ "$INSTALL_DEV" = "true" ] ; then \
        echo "Installing with dev dependencies..." \
        && poetry install --no-root --verbose; \
    else \
        echo "Installing without dev dependencies..." \
        && poetry install --only=main --no-root --verbose; \
    fi

# Copy application code (excluding files in .dockerignore)
COPY . .

# For development - keeps container alive
CMD if [ "$INSTALL_DEV" = "true" ] ; then \
        tail -f /dev/null ; \
    else \
        python src/main.py ; \
    fi
