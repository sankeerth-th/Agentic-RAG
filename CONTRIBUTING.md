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

A00 contains no application setup/tests. S01 supplies the exact uv/pnpm commands,
Compose services, environment example, migrations, contract generation and checks
before its PR. Do not treat future feature descriptions as working endpoints.

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
