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
    mvp1_spec: ./docs/MVP1_noyau_statique.md
    dev_setup: ./docs/README-dev.md
  tags: [raip, readme, eu-ai-act]
last_reviewed: "2026-05-12"
---

# RAIP - Responsible AI in Practice

Ce dépôt regroupe la **documentation** (dossier [`docs/`](docs/README.md)) et un **socle logiciel MVP1** (`src/raip/`) pour une plateforme d’évaluation d’IA responsable alignée sur l’EU AI Act.

## Documentation

- **Index** : [docs/README.md](docs/README.md)
- **Hub** : [docs/ROADMAP.md](docs/ROADMAP.md)
- **MVP1** : [docs/MVP1_noyau_statique.md](docs/MVP1_noyau_statique.md)
- **Setup dev / tests** : [docs/README-dev.md](docs/README-dev.md)
- **Règles assistants IA** : [docs/CLAUDE.md](docs/CLAUDE.md)

## Périmètre code (MVP2)

- CLI `raip-eval`, FastAPI, Celery, LangGraph, LiteLLM → **Ollama** (`ollama/llama3.1:8b-instruct-q8_0`), benchmarks dynamiques, MLflow, MinIO.

## Tests

Voir [docs/README-dev.md](docs/README-dev.md) (pyramide unit / integration / e2e, sans `unittest.mock`).

## Démarrage rapide (MVP2)

1. `ollama pull llama3.1:8b-instruct-q8_0`
2. `cp .env.example .env` et adapter.
3. `docker compose up --build`
4. `pip install -e ".[dev]"` puis `raip-eval run examples/mvp2_ollama_e2e.yaml`

Migration depuis MVP1 : [docs/MIGRATION_MVP1_MVP2.md](docs/MIGRATION_MVP1_MVP2.md).

Les poids Ollama sont sous `~/.ollama/models` ; RAIP utilise l’**API HTTP** Ollama (`OLLAMA_API_BASE`).

## Notes

- Benchmarks **dynamiques** (MVP2) ; voir [docs/MIGRATION_MVP1_MVP2.md](docs/MIGRATION_MVP1_MVP2.md) et la spec [MVP1](docs/MVP1_noyau_statique.md) pour le catalogue COMPL-AI.
