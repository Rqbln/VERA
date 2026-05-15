---
doc:
  title: "Index de la documentation RAIP"
  slug: docs-index
  language: fr
  summary: |
    Point d'entrée pour humains et agents : hub roadmap, MVP1–4, références recherche, guide dev, règles CLAUDE.
  type: index
  audience: [human, developer, compliance, ai-agent]
  navigation:
    root_readme: ../README.md
    primary_hub: ./ROADMAP.md
  children:
    - ./ROADMAP.md
    - ./MVP1_noyau_statique.md
    - ./MVP2_laboratoire_injection.md
    - ./MVP3_dashboards_rbac.md
    - ./MVP4_governance_as_a_service.md
    - ./framework_open_source_ia_responsable.md
    - ./Évaluation Modulaire IA Cycle Vie EU AI Act.md
    - ./README-dev.md
    - ./CLAUDE.md
    - ./donnees_parametres_pilote_mvp1.md
  artifacts:
    - ./2410.07959v2.pdf
  tags: [raip, documentation, index, eu-ai-act]
last_reviewed: "2026-05-12"
---

# Documentation RAIP

Tous les fichiers de ce dossier commencent par un **bloc YAML (front matter)** décrivant titre, résumé, type, navigation et tags pour faciliter l’orientation des outils et modèles.

| Fichier | Rôle |
|--------|------|
| [ROADMAP.md](./ROADMAP.md) | Vision, stack, schéma `benchmark_run`, mapping AI Act, Gantt |
| [MVP1_noyau_statique.md](./MVP1_noyau_statique.md) | MVP1 — noyau d’évaluation inférence |
| [MVP2_laboratoire_injection.md](./MVP2_laboratoire_injection.md) | MVP2 — labo injection / cycle de vie |
| [MVP3_dashboards_rbac.md](./MVP3_dashboards_rbac.md) | MVP3 — dashboards & RBAC |
| [MVP4_governance_as_a_service.md](./MVP4_governance_as_a_service.md) | MVP4 — GaaS production |
| [framework_open_source_ia_responsable.md](./framework_open_source_ia_responsable.md) | Cadrage framework IA responsable |
| [Évaluation Modulaire IA Cycle Vie EU AI Act.md](./Évaluation%20Modulaire%20IA%20Cycle%20Vie%20EU%20AI%20Act.md) | Rapport de recherche |
| [README-dev.md](./README-dev.md) | Setup développeur & tests |
| [CLAUDE.md](./CLAUDE.md) | Règles pour assistants IA (Cursor / Claude Code) |
| [donnees_parametres_pilote_mvp1.md](./donnees_parametres_pilote_mvp1.md) | Paramètres pilote MVP1 (Ollama local, 8 blocs) |
| [2410.07959v2.pdf](./2410.07959v2.pdf) | COMPL-AI (source académique) |

Le [README racine](../README.md) résume le dépôt (code + liens vers cette documentation).
