FROM --platform=linux/amd64 python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install ".[silver]"

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER appuser

ENTRYPOINT ["python", "-m", "nba_pipeline"]
CMD ["--days-back", "10"]
