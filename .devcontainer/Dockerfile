FROM mcr.microsoft.com/devcontainers/python:3.12

COPY pyproject.toml /tmp/build/
COPY src/__init__.py /tmp/build/src/
RUN cd /tmp/build && pip install --no-cache-dir '.[notebook]' && rm -rf /tmp/build
