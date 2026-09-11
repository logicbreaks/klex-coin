# KLEX node image — multi-stage, non-root, slim
FROM python:3.12-slim

LABEL org.opencontainers.image.title="klex-coin" \
      org.opencontainers.image.description="KLEX: post-quantum, fair-launch proof-of-work coin" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY klex/ ./klex/
COPY tests/ ./tests/

RUN useradd --create-home --shell /usr/sbin/nologin klex \
    && mkdir -p /data && chown -R klex:klex /app /data
USER klex
ENV KLEX_HOME=/data
ENV PYTHONUNBUFFERED=1

# Chain data persists here; mount a volume.
VOLUME ["/data"]

# Default: initialize (idempotent) then show status. Override the command:
#   docker run klex-coin python -m klex mine
CMD ["sh", "-c", "python -m klex init || true; python -m klex info"]