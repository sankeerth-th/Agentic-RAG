# Engineering rules

Read ARCHITECTURE.md, CONTRIBUTING.md, the assigned task and shared contracts before
implementation. Architecture baseline **A1 — FROZEN**; intentional changes require
an architecture proposal, impact review, Graphify, Sai approval and a new baseline.

## Ownership and scope

- Sai: `packages/rag_core/`, `workers/ingestion/`, API core and dataset/retrieval/RAG
  modules, initial migrations and integration.
- Vishnu: `apps/web/`, `packages/evaluation/`, `workers/experiments/`, API experiment
  and evaluation modules, benchmark execution and associated tests.
- Controlled: root configuration/docs, `packages/contracts/`, migrations,
  `.github/`, `infra/` and HTTP contracts. Coordinate changes after parallel work
  starts. Do not implement another owner's tasks without reassignment.
- A00 is the one-time empty-repository direct-main bootstrap. S01 is authorized
  only through PR creation and independent review; S02 and V01 need later authority.

## Required workflows

Use official Ponytail FULL, Graphify and obra/Superpowers. Inventory existing tools
before installing. Apply Superpowers planning, TDD, debugging and verification as
appropriate; preserve one useful task specification, not duplicate reports.
Prefer standard libraries, native constraints and existing dependencies. Keep
validation, error handling, security, accessibility and data integrity.

Use `work/<developer>/<task-id>-<description>` branches. Fetch and synchronize with
`origin/main` before starting and before **every push**, including architecture-only
pushes. Never force-push main or push feature implementations directly to it.

## Graphify

If `graphify-out/graph.json` exists, run `graphify query "<question>"`,
`graphify explain "<concept>"` or `graphify path "<A>" "<B>"` before broad source
reads. Use `graphify-out/wiki/index.md` when present for broad navigation; read the
full report only for architecture review or insufficient query results. Dirty
graph artifacts are expected and do not disable this workflow.

After code changes run `graphify update .` when practical. Before every push,
extract the current code AND architecture documents:

```sh
OLLAMA_API_KEY=local OLLAMA_MODEL=gemma3:12b graphify extract . --backend ollama --model gemma3:12b --max-concurrency 1
```

Inspect dependencies, cycles, duplicate components, module coupling, ownership and
contract impacts. Graphify supplies evidence, not proof of correctness. Never
invent edges or treat inferred relationships as actual imports. Respect
`.graphifyignore`; never ingest secrets or source datasets into the graph.
**Graphify failure blocks push.** Keep graph output local and record meaningful
findings in the PR.

## Contracts, checks and review

Python/Pydantic domain schemas are canonical. FastAPI OpenAPI defines implemented
HTTP routes under `/api/v1/`, plus `/health` and `/ready`. Generate TypeScript from
OpenAPI; never maintain parallel handwritten API models. Contract changes require
explicit review. Do not expose speculative endpoints as working functionality.

Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`,
`uv run pytest tests/unit tests/contract`, `pnpm contracts:check` and
`uv build --all-packages`. With local services initialized, run `uv run alembic check`,
`uv run pytest tests/integration` and `uv run python scripts/smoke_processes.py`.
See CONTRIBUTING.md for setup and disposable-database migration checks.
Run those checks, a Ponytail review and full diff
review after Graphify and before pushing. Use deterministic small test fixtures;
large datasets and provider calls do not belong in normal CI. Never commit `.env`,
credentials, secrets, raw corpora, generated caches or debug artifacts.

Task states: ASSIGNED → WORKING → LOCAL_VALIDATION → GRAPHIFY_VALIDATION → PUSHED →
PR_OPEN → REVIEW_PENDING. Rework: CHANGES_REQUESTED → REWORKING → validations →
PR_UPDATED → REVIEW_PENDING. Approval: APPROVED → MERGED → POST_MERGE_VERIFY → DONE;
failed post-merge checks mean POST_MERGE_FAILURE, not DONE.

Sai reviews Vishnu PRs independently, with APPROVE / REQUEST_CHANGES / BLOCKED.
Sai-authored substantive PRs require an authorized independent reviewer and remain
REVIEW_PENDING_INDEPENDENT while one is unavailable. Technical self-review is not
GitHub approval. Sai retains merge authority. Do not weaken branch protection.
After merges, validate clean current main, Graphify, tests, contracts and relevant
build/integration checks before dependent work proceeds.
