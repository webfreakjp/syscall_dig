FROM golang:1.24-bookworm

RUN apt-get update && apt-get install -y \
    git gcc g++ make pkg-config libseccomp-dev python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY scripts/install-python-deps.sh /usr/local/bin/install-python-deps
COPY scripts/copy-sandbox-runtime.sh /usr/local/bin/copy-sandbox-runtime
RUN chmod +x /usr/local/bin/install-python-deps /usr/local/bin/copy-sandbox-runtime

RUN git clone https://github.com/langgenius/dify-sandbox.git . && \
    ./build/build_amd64.sh && \
    mkdir -p /var/sandbox/sandbox-python && \
    cp internal/core/runner/python/python.so /var/sandbox/sandbox-python/ && \
    copy-sandbox-runtime internal/static/config_default_amd64.go /var/sandbox/sandbox-python
