# vldmcp base image: Ubuntu + Python + nginx + podman + (Veilid client/server)
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Base deps
RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    nginx ca-certificates curl gnupg \
    podman tini; \
  rm -rf /var/lib/apt/lists/*

# --- Veilid APT repo (fill in the actual repo+key you use) -------------------
# NOTE: replace the placeholders below with Veilid’s real repo/key.
# RUN set -eux; \
#   curl -fsSL "https://<VEILID_REPO>/gpg.key" | gpg --dearmor -o /etc/apt/trusted.gpg.d/veilid.gpg; \
#   echo "deb [signed-by=/etc/apt/trusted.gpg.d/veilid.gpg] https://<VEILID_REPO>/apt stable main" \
#     > /etc/apt/sources.list.d/veilid.list; \
#   apt-get update; \
#   apt-get install -y --no-install-recommends veilid veilid-cli; \
#   rm -rf /var/lib/apt/lists/*

# App dir
WORKDIR /opt/mcpvld
COPY . /opt/mcpvld

# Nginx config
COPY deploy/nginx/mcpvld.conf /etc/nginx/conf.d/mcpvld.conf
# Drop the default site
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default || true

# Static data root (Ubuntu default for www-data)
RUN mkdir -p /var/www/html && chown -R www-data:www-data /var/www/html

# Simple healthcheck endpoint via nginx
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://127.0.0.1:8080/status || exit 1

# Expose: 8080 (nginx), 8000 (FastAPI default, local only), Veilid default if you enable it
EXPOSE 8080

# Run nginx in foreground; your FastAPI should bind :8000 inside the container.
# Tip: in dev, `podman run ... sh -lc "uvicorn app:app --host 127.0.0.1 --port 8000 & nginx -g 'daemon off;'"`.
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["nginx","-g","daemon off;"]
