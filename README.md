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

## Périmètre code (MVP1)

- CLI `raip-eval`, FastAPI, Celery, LangGraph, LiteLLM → **Ollama** (ex. `ollama/ministral-3:3b`), MLflow, MinIO.

## Tests

Voir [docs/README-dev.md](docs/README-dev.md) (`pytest tests/ -q`, smoke Ollama optionnel).

## Démarrage rapide (MVP1)

1. Ollama sur l’hôte avec le modèle cible (`ollama list` → ajuster `RAIP_TARGET_MODEL` si besoin).
2. `cp .env.example .env` et adapter.
3. `docker compose up --build`
4. `pip install -e .` puis `raip-eval run configs/example.run.yaml`

Les poids Ollama sont sous `~/.ollama/models` ; RAIP utilise l’**API HTTP** Ollama (`OLLAMA_API_BASE`).

## Notes

- Le socle Python implémente encore des **benchmarks stub** ; le catalogue complet est décrit dans la spec MVP1.
