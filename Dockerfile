# Dockerfile for building a Python 3.12.3 image with OpenSSL 3.4.1
# reason: api.ssrn.com uses cloudflare and this triggers anti-bot protection with the default OpenSSL version in Ubuntu 22.04

# Build stage - compile Python with  OpenSSL 3.4.1
FROM ubuntu:22.04 as builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    wget \
    ca-certificates \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Install latest OpenSSL from source
RUN wget https://www.openssl.org/source/openssl-3.4.1.tar.gz && \
    tar -xzf openssl-3.4.1.tar.gz && \
    cd openssl-3.4.1 && \
    ./config --prefix=/usr/local --openssldir=/usr/local/ssl shared && \
    make -j$(nproc) && \
    make install_sw && \
    echo "/usr/local/lib" > /etc/ld.so.conf.d/openssl.conf && \
    echo "/usr/local/lib64" >> /etc/ld.so.conf.d/openssl.conf && \
    ldconfig -v && \
    cd .. && rm -rf openssl-3.4.1*

# Copy system CA certificates to custom OpenSSL directory
RUN mkdir -p /usr/local/ssl/certs && \
    cp /etc/ssl/certs/ca-certificates.crt /usr/local/ssl/certs/ && \
    ln -sf /etc/ssl/certs/ca-certificates.crt /usr/local/ssl/cert.pem

# Set environment variables for OpenSSL before Python compilation
ENV CPPFLAGS="-I/usr/local/include"
ENV LDFLAGS="-L/usr/local/lib -L/usr/local/lib64"
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:${LD_LIBRARY_PATH}"
ENV PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig"

# Compile Python against new OpenSSL
RUN wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz && \
    tar -xzf Python-3.12.3.tgz && \
    cd Python-3.12.3 && \
    ./configure \
        --prefix=/usr/local \
        --with-openssl=/usr/local \
        --with-openssl-rpath=auto \
        --enable-optimizations \
        --with-system-ffi \
        --with-computed-gotos \
        --enable-loadable-sqlite-extensions \
        --with-ssl-default-suites=openssl && \
    make -j$(nproc) && \
    make altinstall && \
    cd .. && rm -rf Python-3.12.3*

# Verify SSL support in Python
RUN /usr/local/bin/python3.12 -c "import ssl; print('SSL support:', ssl.OPENSSL_VERSION)"

# Runtime stage
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

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

# Set library paths for custom OpenSSL
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib64:${LD_LIBRARY_PATH}"
# Set SSL certificate paths
ENV SSL_CERT_FILE="/usr/local/ssl/cert.pem"
ENV SSL_CERT_DIR="/usr/local/ssl/certs"
# Add local bin to PATH
ENV PATH="/usr/local/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled Python and OpenSSL from builder stage
COPY --from=builder /usr/local /usr/local

# Update library cache and ensure SSL cert directory exists
RUN ldconfig && \
    mkdir -p /usr/local/ssl/certs && \
    ln -sf /etc/ssl/certs/ca-certificates.crt /usr/local/ssl/cert.pem

# Create symlinks for python3.12
RUN ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/python3.12 /usr/local/bin/python

# Install git and Node.js for development
RUN if [ "$INSTALL_DEV" = "true" ] ; then \
        apt-get update && \
        apt-get install -y git && \
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
        apt-get install -y nodejs && \
        rm -rf /var/lib/apt/lists/* ; \
    fi

# Install MCP Inspector and claude code for development
RUN if [ "$INSTALL_DEV" = "true" ] ; then \
  npm install -g @modelcontextprotocol/inspector && \
  npm install -g @anthropic-ai/claude-code ; \
fi

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