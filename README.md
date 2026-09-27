# Agentic RAG Lab

Production-oriented RAG engineering and evaluation platform. Compare reproducible
pipelines against pinned dataset versions and questions, inspect retrieval and
generation traces, and measure quality, citations, usage, cost and latency.

**Architecture baseline: A1 — FROZEN.** S01 provides the backend foundation:
FastAPI health/readiness, PostgreSQL schema/migrations, Qdrant/Redis/S3 clients,
Celery worker startup, canonical domain schemas and generated TypeScript contracts.
No retrieval, evaluation or product UI is implemented yet. S01 remains subject to
independent review before merge.

Start with [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md), then
[CONTRIBUTING.md](CONTRIBUTING.md).

Sai Sankeerth Thallapally owns architecture, RAG/retrieval and integration.
Vishnu Yempalla owns evaluation, experiments and web implementation. Shared
contracts are established in S01 before their dependent work begins.

Roadmap: A00 governance → S01 foundation → S02 ingestion / V01 web and evaluation
foundation → S03 retrieval / V02 benchmarks → S04 advanced RAG / V03 studio and
traces → V04 comparisons → S05 hardening → I01 integration → I02 audit.

Capacity and performance claims require measured evidence. This repository does
not currently claim a tested corpus size, retrieval score, latency or cost.

## Run locally

Requires Python 3.12, uv, Node 22, pnpm 10.30.3 and Docker Compose. From the repository root:

```sh
cp .env.example .env
uv sync --all-packages --frozen
pnpm install --frozen-lockfile
docker compose --env-file .env -f infra/compose.yaml up -d --build --wait
uv run alembic upgrade head
uv run python scripts/init_storage.py
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open [API documentation](http://127.0.0.1:8000/docs),
[health](http://127.0.0.1:8000/health) or [readiness](http://127.0.0.1:8000/ready).
Readiness checks all four services, including the migration revision and source
bucket. It returns 503 while a required dependency is unavailable. Timeouts are
bounded per client; probes run sequentially, so outage latency can add across clients.

In another terminal, `uv run celery -A ingestion_worker.app:app worker --concurrency=1`
starts the ingestion queue consumer. S01 registers no ingestion business tasks.
Run `uv run python scripts/smoke_processes.py` to start and verify temporary API
and worker processes, then clean them up automatically.

MinIO community is archived and now source-only. Compose builds its final
[security release](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z)
from pinned source, using pinned build/runtime images. This is local development
wiring; select a maintained S3 service through architecture review before production.
The initial build downloads Go dependencies and can take several minutes.
