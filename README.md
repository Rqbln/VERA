---
doc:
  title: "RAIP — README racine (aperçu dépôt)"
  slug: root-readme
  language: fr
  summary: |
    Aperçu du dépôt Responsible AI in Practice : lien vers la documentation dans docs/, code MVP1, démarrage rapide.
  type: index
  audience: [human, developer, ai-agent]
  navigation:
    documentation: ./docs/README.md
    roadmap: ./docs/ROADMAP.md
    agents: ./AGENTS.md
    user_guide: ./USER_GUIDE.md
    dev_setup: ./docs/README-dev.md
  tags: [raip, readme, eu-ai-act]
last_reviewed: "2026-06-15"
---

# RAIP - Responsible AI in Practice

Ce dépôt regroupe la **documentation** (dossier [`docs/`](docs/README.md)) et un **socle logiciel** (`src/raip/` + `dashboard/`) pour une plateforme d’évaluation d’IA responsable alignée sur l’EU AI Act.

## Documentation

- **Agents IA** : [AGENTS.md](AGENTS.md) — orientation, architecture, quickstart
- **Utilisateurs non techniques** : [USER_GUIDE.md](USER_GUIDE.md) — guide pas-à-pas
- **Index** : [docs/README.md](docs/README.md) · **Hub** : [docs/ROADMAP.md](docs/ROADMAP.md)
- **Setup dev / tests** : [docs/README-dev.md](docs/README-dev.md)
- **État MVP3/MVP4** : [docs/MVP3_MVP4_IMPLEMENTATION.md](docs/MVP3_MVP4_IMPLEMENTATION.md)

## Périmètre code

- CLI `raip-eval`, FastAPI, Celery, LangGraph, LiteLLM → **Ollama** (`ollama/llama3.1:8b-instruct-q8_0`), benchmarks dynamiques, MLflow, MinIO ; **dashboard Next.js** (control room + mode guidé).

## Démarrage rapide

**Mode guidé / lite (une commande, sans login)** — pour démos et utilisateurs non techniques :

1. `ollama pull llama3.1:8b-instruct-q8_0`
2. `make quickstart` → ouvrir **http://localhost:3000** (voir [USER_GUIDE.md](USER_GUIDE.md))

**Mode complet (entreprise, RBAC Keycloak + MLflow + MinIO)** :

1. `cp .env.example .env` et adapter ; `make stack-full` (= `docker compose up --build`)
2. `pip install -e ".[dev]"` puis `raip-eval run examples/mvp2_ollama_e2e.yaml`

**Mode gouvernance (MVP4 GaaS)** — runtime de gouvernance de l'inférence en direct :

1. `make stack-gaas` → stack complète + proxy inline (`:8100`), Redpanda, OPA, OpenSearch, agents
2. Page **/governance** dans le dashboard ; guide : [docs/MVP4_GAAS_RUNTIME.md](docs/MVP4_GAAS_RUNTIME.md)

Migration depuis MVP1 : [docs/MIGRATION_MVP1_MVP2.md](docs/MIGRATION_MVP1_MVP2.md).
Design system + bilingue FR/EN du dashboard : [dashboard/DESIGN_SYSTEM.md](dashboard/DESIGN_SYSTEM.md).

## Tests

Voir [docs/README-dev.md](docs/README-dev.md) (pyramide unit / integration / e2e + Playwright, sans `unittest.mock`).

Les poids Ollama sont sous `~/.ollama/models` ; RAIP utilise l’**API HTTP** Ollama (`OLLAMA_API_BASE`).

## Notes

- Benchmarks **dynamiques** (MVP2) ; voir [docs/MIGRATION_MVP1_MVP2.md](docs/MIGRATION_MVP1_MVP2.md) et la spec [MVP1](docs/MVP1_noyau_statique.md) pour le catalogue COMPL-AI.
