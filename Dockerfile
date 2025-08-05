FROM python:3.10-bookworm

WORKDIR /usr/src/vulnhuntr

# Copy everything (ensure .dockerignore is properly configured)
COPY . .

# Install with increased timeout and retries
RUN pip install --no-cache-dir --timeout 600 --retries 10 .

ENTRYPOINT [ "vulnhuntr" ]