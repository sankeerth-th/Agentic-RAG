# Agentic RAG Lab

Production-oriented RAG engineering and evaluation platform. Compare reproducible
pipelines against pinned dataset versions and questions, inspect retrieval and
generation traces, and measure quality, citations, usage, cost and latency.

**Architecture baseline: A1 — FROZEN.** This bootstrap contains governance and
architecture only. S01 adds the runnable backend foundation through a reviewed PR.
No retrieval, evaluation or product UI is implemented yet.

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
