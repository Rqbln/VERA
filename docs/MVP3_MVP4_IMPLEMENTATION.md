---
doc:
  title: "MVP3 / MVP4 — état d'implémentation"
  slug: mvp3-mvp4-implementation
  language: fr
  summary: |
    Matrice « ce qui est réellement construit » pour MVP3 (dashboards, HITL, formulaires, PDF signé)
    et la tranche fine MVP4 (Trust Factor, dérive, kill-switch). Source de vérité unique côté code.
  type: status
  audience: [developer, ai-agent, compliance]
  navigation:
    hub: ./ROADMAP.md
    mvp3: ./MVP3_dashboards_rbac.md
    mvp4: ./MVP4_governance_as_a_service.md
    agents: ../AGENTS.md
  tags: [raip, mvp3, mvp4, status]
last_reviewed: "2026-06-15"
---

# MVP3 / MVP4 — état d'implémentation

> Voir [ROADMAP.md](./ROADMAP.md) · Pré-requis : MVP1, MVP2.
> Cette matrice reflète le code de la branche `mvp3-mvp4`. Statuts : `done` (livré), `partial`
> (livré avec limites), `deferred` (volontairement reporté).

## Socle : simplification & mode guidé

| Fonctionnalité | Statut | Module / route | Note |
|----------------|--------|----------------|------|
| Mode guidé sans login (défaut) | `done` | `api/auth.py` (`RAIP_AUTH_MODE=guided`), `dashboard/src/lib/auth.ts` (`isGuided`) | Persona unique = union de tous les rôles ; RBAC intacte en `enterprise` |
| Stack « lite » une commande | `done` | `docker-compose.lite.yml`, `Makefile` (`make quickstart`) | Redis + API + worker + dashboard uniquement |
| Artefacts locaux (sans MinIO) | `done` | `artifacts/local_fs.py`, `artifacts/s3io.py` (`artifact_backend`) | Bascule auto `minio`→`local` |
| MLflow optionnel | `done` | `tasks/eval.py` (garde `mlflow_enabled`) | Le worker ne plante plus sans MLflow |
| Santé du stack tri-état | `done` | `dashboard_routes.py::health_stack` | requis (rouge) vs optionnel (orange) |

## MVP3 — dashboards, HITL, formulaires

| Fonctionnalité | Statut | Module / route | Note |
|----------------|--------|----------------|------|
| Registre de modèles connectés | `done` | `api/models_routes.py`, `store/redis_models.py` | `GET /models/connected` via tags Ollama |
| Assistant de lancement (UI) | `done` | `dashboard/.../LaunchWizard.tsx`, `app/(console)/launch` | 4 étapes → `POST /api/v1/runs` |
| Accueil guidé | `done` | `HomeOverview.tsx`, `app/(console)/home` | « ce que vous pouvez faire » |
| Tableau récapitulatif des runs | `done` | `RunsOverviewTable.tsx`, `dashboard_routes.py` (`include_triage`) | triage + score en tête |
| Courbes longitudinales | `done` | `/series`, `TrendCurve.tsx` | dérivé des runs Redis ; pas de fausse série < 2 points |
| HITL N01 / N02 | `done` | `store/redis_hitl.py`, `/hitl/tasks`, `HitlReviewPanel.tsx` | file de revue + Likert 1–5 |
| Formulaires déclaratifs N03–N06 | `done` | `schemas/declarative_forms.py`, `forms_routes.py`, `DeclarativeForms.tsx` | persistés par run |
| Export PDF d'audit signé | `partial` | `governance/pdf_export.py`, `GET /runs/{id}/audit-pdf` | sha256 self-attestation ; WeasyPrint optionnel (extra `pdf`) ; **pas** de signature eIDAS / TSA RFC 3161 |
| 3 vues RBAC (compliance/cyber/ds) | `done` | `app/dashboards/*` | inchangées ; persona guidé passe les 3 lentilles |
| Matrice RBAC Playwright | `done` | `dashboard/e2e/control-room.spec.ts` + `guided-mode.spec.ts` | 25 + 5 tests |

## MVP4 — tranche fine (gouvernance sur l'infra existante)

| Fonctionnalité | Statut | Module / route | Note |
|----------------|--------|----------------|------|
| Trust Factor (0–100) | `done` | `governance/trust_factor.py`, `TrustFactorCard.tsx` | agrégation pondérée R01/R02/R05/R12, configurable |
| Détection de dérive (à la demande) | `done` | `tasks/monitor.py`, `GET /monitor/drift` | dernier run vs moyenne glissante ; pas de canary planifié |
| Kill-switch | `done` | `governance/kill_switch.py`, `/governance/kill-switch`, `KillSwitchToggle.tsx` | bloque `POST /runs` (503) + court-circuite le worker |

## Reporté (deferred) — gouvernance-as-a-service complète

Volontairement hors périmètre (contradictoire avec l'objectif de simplification) ; voir
[MVP4_governance_as_a_service.md](./MVP4_governance_as_a_service.md) pour la cible complète :

- Proxy asynchrone inline en production (httpx + shadow inspection < 10 ms).
- Bus d'événements **Kafka** + schema registry.
- Moteur de politiques **OPA / Rego**.
- Passerelle **Kong / Envoy** + feature flags **Unleash**.
- SIEM **Wazuh / OpenSearch**, détection de dérive par embeddings (Evidently/NannyML).
- Canary planifié (200 prompts/heure) — ici remplacé par une vérification de dérive à la demande.

## Limites à traiter côté opérateur

1. **Signature qualifiée** (eIDAS / horodatage RFC 3161) : nécessite un TSA externe + clé gérée
   (OpenBao/Cosign). Livré : empreinte sha256 vérifiable seulement.
2. **Keycloak production** (realm durci, secrets, HTTPS) pour le mode `enterprise`.
3. **WeasyPrint** : `pip install '.[pdf]'` + bibliothèques système cairo/pango.
4. **Stack GaaS complète** : projet d'infrastructure séparé (cf. liste « reporté »).

## Tests (dernière exécution locale)

- `pytest tests/unit/` — 71 passés (Redis requis).
- `npx playwright test` — 30 passés (25 RBAC + 5 mode guidé).
- `ruff check` — propre sur les nouveaux modules.
