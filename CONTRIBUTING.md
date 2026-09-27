# Contributing

```sh
git clone https://github.com/sankeerth-th/Agentic-RAG.git
cd Agentic-RAG
```

Read AGENTS.md, ARCHITECTURE.md, your task specification, then shared contracts.
Verify Git identity/authentication without printing tokens. Required tools: Python
3.12+, uv, Git/GitHub CLI, Node, pnpm, Docker with Compose, Ponytail FULL, Graphify
(`graphifyy`, official Graphify-Labs/graphify) and obra/Superpowers. Reuse existing
installations; verify official instructions before installing missing tools.

Follow README.md for a fresh setup. Keep commands at the repository root. Python
workspace members are the API, contracts and ingestion worker. The web workspace
is intentionally absent until Vishnu's V01 assignment. Node is used only for
contract generation/type checks in S01. The task specification is
[docs/tasks/S01.md](docs/tasks/S01.md).

## Local checks

```sh
uv sync --all-packages --frozen
pnpm install --frozen-lockfile
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest tests/unit tests/contract
pnpm contracts:check
uv build --all-packages
```

After starting local services and running migrations/bucket initialization:

```sh
uv run alembic check
uv run pytest tests/integration
uv run python scripts/smoke_processes.py
```

CI additionally exercises `alembic downgrade base` followed by `alembic upgrade
head` against a disposable database. **Downgrade deletes schema/data**; do not use
that check against a database you need to keep. Integration tests insert tiny
transactional fixtures and remove their temporary S3 object.

Compose uses project-specific named volumes and loopback ports: PostgreSQL 55432,
Redis 56379, Qdrant 56333, MinIO S3 59000 and console 59001. Stop with
`docker compose -f infra/compose.yaml down`; add `--volumes` only to discard local
service data. Qdrant availability is tested through its authenticated client API
by `/ready` and integration tests rather than a shell probe inside the image.

## Shared contracts and schema

Edit Python/Pydantic schemas, then run `pnpm contracts:generate` and
`pnpm contracts:check`. Commit both `packages/contracts/openapi.json` and
`packages/contracts/generated/api.d.ts`. Consumers import
`@agentic-rag/contracts` types. Reusable domain schemas are OpenAPI components;
the only implemented operations in S01 are `/health` and `/ready`.

Configuration mappings use read-only proxies and tuples internally and serialize
as ordinary JSON objects/arrays. Serialize snapshots at persistence boundaries;
PostgreSQL triggers reject updates
and deletes of published snapshots. Query/experiment run configuration is also
protected while operational status/results can advance. Source document sets are
pinned by the immutable version manifest/hash; S02 must validate manifest membership
when materializing documents/chunks. S01 does not implement that ingestion lifecycle.

Configuration JSON in PostgreSQL must be validated with the canonical schemas at
future write boundaries. Database constraints enforce identities, scopes, hashes,
counts and uniqueness, not the full Pydantic JSON shape. Migrations are versioned
snapshots; never import current metadata into a historical migration. After a
reviewed schema change use `uv run alembic revision --autogenerate -m 'description'`,
inspect its output and add explicit trigger/data migrations as needed.

## Git and review

```sh
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c work/sai/S01-platform-foundation
```

Use `work/<developer>/<task-id>-<description>` for later assignments. Before every
push, fetch main and merge current `origin/main` into the task branch when needed;
resolve conflicts and rerun validation. Avoid rewriting shared feature history.

Run the Graphify command in AGENTS.md on the current repository; inspect architecture,
dependencies and ownership. Then run task tests/checks, relevant builds, contract
verification, Ponytail review and complete diff review. Graphify failure blocks push.
Do not commit raw corpora, local service data, caches, graph output or secrets.

Open a PR using the repository template. Give exact verification results and real
limitations. Do not download large datasets in CI. Reviewers inspect actual code,
contracts, migrations, dependencies and tests, not just the PR description.

Sai reviews Vishnu PRs; Vishnu or another explicitly authorized independent reviewer
reviews substantive Sai PRs. Sai alone is merge authority. Do not require Sai's own
CODEOWNER approval on Sai-authored PRs: GitHub cannot satisfy that requirement.
Unavailable independent review means REVIEW_PENDING_INDEPENDENT.

Requested changes remain with the author on the same branch and PR. Repeat Graphify
and validation before updates. After merge, verify clean latest main, migrations,
contracts, tests, Graphify and relevant service/build checks before marking DONE.
