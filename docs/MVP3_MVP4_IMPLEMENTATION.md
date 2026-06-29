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
  tags: [vera, mvp3, mvp4, status]
last_reviewed: "2026-06-26"
---

# MVP3 / MVP4 — état d'implémentation

> Voir [ROADMAP.md](./ROADMAP.md) · Pré-requis : MVP1, MVP2.
> Cette matrice reflète le code de la branche `mvp3-mvp4`. Statuts : `done` (livré), `partial`
> (livré avec limites), `deferred` (volontairement reporté).

## Socle : simplification & mode guidé

| Fonctionnalité | Statut | Module / route | Note |
|----------------|--------|----------------|------|
| Mode guidé sans login (défaut) | `done` | `api/auth.py` (`VERA_AUTH_MODE=guided`), `dashboard/src/lib/auth.ts` (`isGuided`) | Persona unique = union de tous les rôles ; RBAC intacte en `enterprise` |
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
| HITL N01 / N02 | `done` | `store/redis_hitl.py`, `/hitl/tasks`, `/hitl/rubrics`, `HitlReviewPanel.tsx` | rubrique multi-critères 1–5 (N01 : faithfulness/completeness/clarity/actionability ; N02 : responsiveness/reversibility/oversight/safety) → Likert moyen ; Likert direct accepté en repli |
| Formulaires déclaratifs N04–N06 | `done` | `schemas/declarative_forms.py`, `forms_routes.py`, `DeclarativeForms.tsx` | persistés par run |
| Énergie N03 (mesurée) | `done` | `governance/energy.py`, `tasks/eval.py` (`_autofill_n03_energy`) | CodeCarbon autour de l'inférence → `kwh`/`co2eq` dans `RunRecord` → formulaire N03 auto-rempli ; dégradation gracieuse si CodeCarbon absent |
| Bandeau N01–N06 (état réel) | `done` | `dashboard_routes.py::_non_measurable_slots`, `NonMeasurableStrip.tsx` | lit `RedisHitlStore` + `RedisFormStore` + `RunRecord.energy` — plus de placeholders statiques |
| Export PDF d'audit signé | `partial` | `governance/pdf_export.py`, `GET /runs/{id}/audit-pdf` | sha256 self-attestation ; WeasyPrint optionnel (extra `pdf`) ; **pas** de signature eIDAS / TSA RFC 3161 |
| 3 vues RBAC (compliance/cyber/ds) | `done` | `app/dashboards/*` | inchangées ; persona guidé passe les 3 lentilles |
| Matrice RBAC Playwright | `done` | `dashboard/e2e/control-room.spec.ts` + `guided-mode.spec.ts` | 25 + 5 tests |

## MVP4 — tranche fine (gouvernance sur l'infra existante)

| Fonctionnalité | Statut | Module / route | Note |
|----------------|--------|----------------|------|
| Trust Factor (0–100) | `done` | `governance/trust_factor.py`, `TrustFactorCard.tsx` | agrégation pondérée R01/R02/R05/R12, configurable |
| Détection de dérive (à la demande) | `done` | `tasks/monitor.py`, `GET /monitor/drift` | dernier run vs moyenne glissante ; pas de canary planifié |
| Kill-switch | `done` | `governance/kill_switch.py`, `/governance/kill-switch`, `KillSwitchToggle.tsx` | bloque `POST /runs` (503) + court-circuite le worker |

## MVP4 — runtime GaaS complet (profil `gaas`)

Runtime de gouvernance réel et exécutable (`make stack-gaas`), opt-in via profil Docker ; la stack
lite reste inchangée. Guide complet : [MVP4_GAAS_RUNTIME.md](./MVP4_GAAS_RUNTIME.md).

| Fonctionnalité | Statut | Module / service | Note |
|---|---|---|---|
| Bus d'événements | `done` | `governance/bus.py` | Redpanda/Kafka, **fallback Redis Streams** |
| Proxy inline (OpenAI-compatible) | `done` | `governance/proxy.py`, `services/proxy/` | gouverne → forward (LiteLLM) → publie ; bloque en `enforcement` |
| 4 agents de scoring | `done` | `governance/agents.py`, `services/agents/` | cyber/ethics/privacy/drift ; Detoxify/Presidio si présents, sinon heuristique |
| Trust Factor en flux | `done` | `governance/trust_stream.py` | agrège `gov-signals` → Redis + Timescale (best-effort) |
| Moteur de politiques OPA | `done` | `governance/policy.py`, `infra/opa/vera.rego` | décision allow/flag/deny ; **fallback intégré** |
| Modes shadow/advisory/enforcement | `done` | `governance/modes.py` | par modèle, Redis |
| Audit / SIEM signé | `done` | `governance/audit.py`, `services/audit_sink/` | OpenSearch + **chaîne JSONL signée** ; incidents |
| Canary planifié | `done` | `tasks/canary.py` (Celery beat) | trafic doré → bus |
| Plan d'admin | `done` | `api/admin_routes.py` | `/admin/v1/{proxy/health,mode,trust,incidents,policy,kill-switch}` |
| Profil `gaas` Docker | `done` | `docker-compose.gaas.yml`, `Dockerfile.gaas`, `make stack-gaas` | redpanda+opa+opensearch+proxy+agents+audit-sink |

## Évaluation native & ancrage banque (branche `mvp4-eval-banking`)

Suite native exécutable de bout en bout pour le papier (3 modèles), corpus bancaire synthétique
pour R03–R05, et mesure du runtime GaaS. Repro : [EVALUATION_GUIDE.md](./EVALUATION_GUIDE.md).

| Fonctionnalité | Statut | Module / script | Note |
|---|---|---|---|
| Harnais natifs installés | `done` | `scripts/setup_native.sh`, extras `.[benchmarks,lab,pdf]` | lm-eval, datasets, detoxify, presidio, Levenshtein/sacrebleu, codecarbon, weasyprint |
| Forçage du natif (anti-fallback) | `done` | `benchmarks/runners/evaluate.py` (`VERA_REQUIRE_NATIVE`) | échec si un runner natif retombe en heuristique ; exception assumée `garak` (`VERA_NATIVE_ALLOW`) |
| R03–R05 exécutées (corpus) | `done` | `scripts/gen_banking_corpus.py`, `data/corpus/banking_synth.jsonl`, `dataset_scan` | CR03 0.84 / CR04 0.94 / CR05 0.73 sur 230 docs synthétiques (PII/quasi-doublons/déséquilibre) |
| Harnais multi-modèles | `done` | `scripts/run_paper_eval.py` | panel séquentiel (qwen/mistral/llama…), `VERA_EVAL_MODELS`/`_N`, JSON consolidé |
| Benchmark du runtime GaaS | `done` | `scripts/bench_gaas.py` | overhead proxy p50 5.7 ms, détection 3/3, OPA enforce + bus Redis-Streams vérifiés |
| Tables/figures du papier | `done` | `manuscript/scripts/gen_paper_multi.py` | table 3×12, sensibilité non dégénérée (CR06/CR10 band-flip), figures optionnelles |
| Caveat serving (Ollama) | `done` | `benchmarks/runners/lm_eval_runner.py` | pas de logprobs → R06/R10 en sondes dynamiques ; natif lm-eval réservé à vLLM (tracé en provenance) |

## Restyle & internationalisation

| Fonctionnalité | Statut | Module | Note |
|---|---|---|---|
| Design system clair BNP-green | `done` | `globals.css`, `tailwind.config.ts`, [`DESIGN_SYSTEM.md`](../dashboard/DESIGN_SYSTEM.md) | tokens brand/ink/surface/status |
| Tuiles KPI · timeline · pictos | `done` | `KpiTiles.tsx`, `Timeline.tsx`, lucide-react | jalon actif = vert vif #76B82A |
| Page gouvernance | `done` | `app/(console)/governance`, `GovernancePanel.tsx` | surface du runtime MVP4 |
| Bilingue FR/EN | `done` | `lib/i18n.tsx`, bascule dans le shell | sigles conservés en anglais |

## Durcissement (à traiter côté opérateur — hors de ce build)

1. **SIEM production** : Wazuh + OpenSearch en cluster + règles de corrélation (ici : OpenSearch
   mono-nœud + journal d'audit signé).
2. **Streaming haut débit** : Flink/Kafka-Streams pour l'agrégation du Trust Factor (ici : consumer
   à fenêtre glissante).
3. **Signature qualifiée** : OpenBao Transit + TSA RFC 3161 / eIDAS (ici : sha256 vérifiable).
4. **Passerelle / mTLS** : Kong ou Envoy devant le proxy + rate-limiting.
5. **Dérive par embeddings** : NannyML/Evidently + golden set maintenu (ici : canary + heuristique).
6. **Keycloak production** (realm durci, secrets, HTTPS) ; **WeasyPrint** (`pip install '.[pdf]'`).

## Tests (dernière exécution locale)

- `pytest tests/unit/` — 104 passés (Redis requis ; inclut bus/agents/proxy/policy/audit/admin
  + `test_native_energy_nonmeasurable.py` : require-native, énergie N03, rubrique HITL, bandeau N).
- `npx playwright test` — 35 passés (25 RBAC + mode guidé + gouvernance + bascule de langue).
- `ruff check` — propre sur les fichiers de la branche (scripts en ignore `E402`/`E501` ; CI ne lance pas ruff).
- `make stack-gaas` — pipeline gouverné de bout en bout (proxy:8100, OPA, Redpanda, OpenSearch).
- `scripts/bench_gaas.py` — overhead proxy + détection + dégradation chiffrés (`manuscript/results/gaas_bench.json`).
