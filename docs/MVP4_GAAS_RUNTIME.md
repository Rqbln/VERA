---
doc:
  title: "MVP4 — Governance-as-a-Service runtime (built)"
  slug: mvp4-gaas-runtime
  language: en
  summary: |
    Operator/developer guide to the governance runtime as actually implemented: inline proxy,
    event bus, scoring agents, streaming Trust Factor, OPA policy, modes, signed audit/SIEM,
    canary, admin API. The `gaas` Docker profile; graceful degradation. Distinct from the
    original vision doc (MVP4_governance_as_a_service.md).
  type: reference
  audience: [developer, ai-agent, compliance, secops]
  navigation:
    hub: ./ROADMAP.md
    vision: ./MVP4_governance_as_a_service.md
    status: ./MVP3_MVP4_IMPLEMENTATION.md
    agents: ../AGENTS.md
  tags: [mvp4, gaas, opa, kafka, redpanda, opensearch, proxy, audit, trust-factor]
last_reviewed: "2026-06-22"
---

# MVP4 — Governance-as-a-Service runtime (built)

> The [original MVP4 vision](./MVP4_governance_as_a_service.md) described the target. **This** doc
> describes what is *actually implemented* on branch `mvp4-gaas`, runnable via `make stack-gaas`.
> The lite/guided stack ([guided](./MVP3_dashboards_rbac.md)) is untouched and stays one command.

## 1. What it is

A real, runnable **governed-inference pipeline** layered around the existing evaluation stack and
opted into via a Docker profile. It reuses the platform's scoring code and degrades gracefully, so
architectural depth and one-command simplicity coexist.

```
                 ┌─────────── synchronous inference (lite & gaas) ───────────┐
   client ⇄ inline proxy ⇄ self-hosted target (Ollama/vLLM)
                    │  ▲ OPA decision + kill-switch/mode (red)
                    ▼  (async copy)
   ┌──────────── asynchronous governance (gaas) ────────────┐
   event bus (Redpanda/Kafka → Redis Streams fallback)
     → agents: cyber(CR02) · ethics(CR12) · privacy(CR05) · drift(CR01)
     → streaming Trust Factor → OPA (live trust feedback)
     → signed audit/SIEM (OpenSearch + signed JSONL)
   canary scheduler → event bus      admin API / control room ← trust, incidents, modes
```

(See `manuscript/` Fig. 2 for the publication diagram.)

## 2. Components (code map)

| Component | Module / service | Role |
|---|---|---|
| Event bus | `src/raip/governance/bus.py` | Kafka/Redpanda or **Redis Streams** fallback; topics `llm-traffic`, `gov-signals`, `audit-events` |
| Modes | `src/raip/governance/modes.py` | per-model `shadow`/`advisory`/`enforcement` in Redis |
| Policy | `src/raip/governance/policy.py` + `infra/opa/raip.rego` | OPA decision `allow`/`flag`/`deny`; built-in equivalent fallback |
| Inline proxy | `src/raip/governance/proxy.py` + `services/proxy/` | OpenAI-compatible; govern → forward → publish |
| Agents | `src/raip/governance/agents.py` + `services/agents/` | 4 scorers (Detoxify/Presidio when present, heuristic fallback) |
| Streaming Trust Factor | `src/raip/governance/trust_stream.py` | folds `gov-signals` → live Trust Factor (Redis + Timescale) |
| Audit / SIEM | `src/raip/governance/audit.py` + `services/audit_sink/` | signed records → OpenSearch + signed JSONL chain; incidents |
| Canary | `src/raip/tasks/canary.py` (Celery beat) | golden traffic → bus |
| Admin API | `src/raip/api/admin_routes.py` | `/admin/v1/{proxy/health,mode,trust,incidents,policy,kill-switch}` |

## 3. Modes

- **shadow** — observe only; never blocks (safe roll-out default).
- **advisory** — raise incidents/alerts; never blocks.
- **enforcement** — block when the kill-switch is engaged or OPA denies (proxy returns `503`).

Set per model: `POST /admin/v1/mode/{model} {"mode": "..."}` or the dashboard `/governance` page.

## 4. Decision contract (OPA / built-in)

```
input  = {model, mode, kill_switch, trust_score (0-1|null), signals}
output = {decision: "allow"|"flag"|"deny", reasons: [...], source: "opa"|"builtin"}
```
Thresholds via `RAIP_POLICY_BLOCK_BELOW` (0.30), `RAIP_POLICY_WARN_BELOW` (0.60).

## 5. Run it

```bash
make stack-gaas      # full stack + redpanda + opa + opensearch + proxy + agents + audit-sink
# send a governed request through the proxy:
curl -s localhost:8100/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"ollama/llama3.1:8b-instruct-q8_0","messages":[{"role":"user","content":"hello"}]}'
# inspect:
curl -s localhost:8000/admin/v1/proxy/health
curl -s localhost:8000/admin/v1/trust/ollama%2Fllama3.1:8b-instruct-q8_0
```

Ports: proxy `:8100`, OPA `:8181`, OpenSearch `:9200`, Redpanda `:9092`.

## 6. Graceful degradation matrix

| External service | Present | Absent (fallback) |
|---|---|---|
| Kafka/Redpanda (`KAFKA_BROKER_URL`) | Kafka bus | **Redis Streams** |
| OPA (`OPA_URL`) | Rego policy | in-process equivalent (`policy.builtin_decision`) |
| OpenSearch (`OPENSEARCH_URL`) | indexed audit | **signed JSONL** chain only |
| TimescaleDB | trust time-points persisted | Redis series only |

## 7. Environment

`RAIP_GAAS_ENABLED`, `KAFKA_BROKER_URL`, `OPA_URL`, `OPENSEARCH_URL`, `RAIP_GOVERNANCE_MODE`
(`shadow`|`advisory`|`enforcement`), `RAIP_CANARY_CRON`, `RAIP_PROXY_TARGET_URL`. See `.env.example`.

## 8. Hardening (operator tasks — not in this build)

Production SIEM (Wazuh + clustered OpenSearch + correlation rules); high-throughput streaming
(Flink/Kafka-Streams); qualified signing (OpenBao Transit + RFC 3161/eIDAS); edge gateway + mTLS
(Kong/Envoy); embedding-drift (NannyML/Evidently with a maintained golden set); the operational
30-day shadow→advisory→enforcement roll-out policy.
