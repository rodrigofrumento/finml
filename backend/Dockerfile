# --- base builder ---
FROM python:3.13 AS deps
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# install Poetry
RUN pip install --upgrade pip && pip install poetry

# copy lock for layer caching
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi --no-root

# --- runtime ---
FROM python:3.13 AS runtime
COPY --from=deps /usr/local /usr/local
COPY app /app/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request,os,sys; url=f'http://127.0.0.1:{os.getenv(\"PORT\",\"8000\")}/health'; \
    r=urllib.request.urlopen(url,timeout=2); sys.exit(0 if r.getcode()==200 else 1)"


USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]