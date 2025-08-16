FROM python:3.11-slim

# Version spec (e.g., "==1.2.3" or ">=1.0.0")
ARG VERSION_SPEC=""

WORKDIR /app

# Install from PyPI
RUN pip install vldmcp${VERSION_SPEC}

CMD ["vldmcpd"]
