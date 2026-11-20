# One image per commit, run unchanged in Fork staging and Fork production.
# It holds the code and the versions in uv.lock, and no setting: each
# environment passes its own at run time (.env.example lists them all).
#
#     docker build -t mathutrice .
#     docker run --env-file .env -p 8000:8000 mathutrice
FROM python:3.14.7-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, in their own layer; the dev group (tach, pytest) stays out.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project
COPY mathutrice ./mathutrice
RUN uv sync --locked --no-dev

# The process writes the SQLite file in /app and uploaded PDFs in
# mathutrice/rag_documents, and nothing else.
RUN useradd --system --no-create-home app \
    && mkdir -p mathutrice/rag_documents \
    && chown app /app mathutrice/rag_documents
USER app
ENV PATH="/app/.venv/bin:$PATH"

# The service is one process: uvicorn serves the app, and the APScheduler job
# that deletes old conversations runs inside it (app.py, lifespan).
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn mathutrice.app:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
