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
    - ../AGENTS.md
    - ../USER_GUIDE.md
    - ./ROADMAP.md
    - ./MVP1_noyau_statique.md
    - ./MVP2_laboratoire_injection.md
    - ./MVP2_ROADMAP_LAB.md
    - ./MVP2_STATUS.md
    - ./mvp2-lab/README.md
    - ./MVP2_LAB_RUNBOOK.md
    - ./MVP3_dashboards_rbac.md
    - ./MVP3_UX_CONTROL_ROOM.md
    - ./MVP3_MVP4_IMPLEMENTATION.md
    - ./MVP4_governance_as_a_service.md
    - ./MIGRATION_MVP1_MVP2.md
    - ./framework_open_source_ia_responsable.md
    - ./Évaluation Modulaire IA Cycle Vie EU AI Act.md
    - ./README-dev.md
    - ./CLAUDE.md
  artifacts:
    - ./2410.07959v2.pdf
  tags: [raip, documentation, index, eu-ai-act]
last_reviewed: "2026-06-15"
---

# Documentation RAIP

Tous les fichiers de ce dossier commencent par un **bloc YAML (front matter)** décrivant titre, résumé, type, navigation et tags pour faciliter l’orientation des outils et modèles.

> **Agents IA** : commencez par [AGENTS.md](../AGENTS.md) (orientation, architecture, quickstart).
> **Utilisateurs non techniques** : voir [USER_GUIDE.md](../USER_GUIDE.md).

| Fichier | Rôle |
|--------|------|
| [AGENTS.md](../AGENTS.md) | Orientation canonique pour agents IA (racine) |
| [USER_GUIDE.md](../USER_GUIDE.md) | Guide utilisateur non technique (mode guidé) |
| [ROADMAP.md](./ROADMAP.md) | Vision, stack, schéma `benchmark_run`, mapping AI Act, Gantt |
| [MVP1_noyau_statique.md](./MVP1_noyau_statique.md) | MVP1 — noyau d’évaluation inférence |
| [MVP2_laboratoire_injection.md](./MVP2_laboratoire_injection.md) | MVP2 — spec labo injection / cycle de vie |
| [MVP2_ROADMAP_LAB.md](./MVP2_ROADMAP_LAB.md) | MVP2 — hub d'exécution phases 0–7 |
| [MVP2_STATUS.md](./MVP2_STATUS.md) | MVP2 — état implémentation 18 exigences |
| [mvp2-lab/](./mvp2-lab/README.md) | MVP2 — fiches phase (détail technique) |
| [MVP2_LAB_RUNBOOK.md](./MVP2_LAB_RUNBOOK.md) | MVP2 — procédures opérationnelles lab |
| [MVP3_dashboards_rbac.md](./MVP3_dashboards_rbac.md) | MVP3 — dashboards & RBAC |
| [MVP3_UX_CONTROL_ROOM.md](./MVP3_UX_CONTROL_ROOM.md) | MVP3 — design UX de la control room |
| [MVP3_MVP4_IMPLEMENTATION.md](./MVP3_MVP4_IMPLEMENTATION.md) | MVP3/MVP4 — **état d'implémentation** (matrice) |
| [MVP4_governance_as_a_service.md](./MVP4_governance_as_a_service.md) | MVP4 — GaaS production (cible/vision) |
| [MVP4_GAAS_RUNTIME.md](./MVP4_GAAS_RUNTIME.md) | MVP4 — **runtime GaaS tel que construit** (proxy, bus, OPA, agents, audit) |
| [MIGRATION_MVP1_MVP2.md](./MIGRATION_MVP1_MVP2.md) | Migration MVP1 → MVP2 |
| [framework_open_source_ia_responsable.md](./framework_open_source_ia_responsable.md) | Cadrage framework IA responsable |
| [Évaluation Modulaire IA Cycle Vie EU AI Act.md](./Évaluation%20Modulaire%20IA%20Cycle%20Vie%20EU%20AI%20Act.md) | Rapport de recherche |
| [README-dev.md](./README-dev.md) | Setup développeur & tests |
| [CLAUDE.md](./CLAUDE.md) | Conventions profondes & graphe documentaire (assistants IA) |
| [2410.07959v2.pdf](./2410.07959v2.pdf) | COMPL-AI (source académique) |

Le [README racine](../README.md) résume le dépôt (code + liens vers cette documentation).
