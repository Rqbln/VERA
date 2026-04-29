# MVP 2 — Laboratoire d'Injection & Cycle de Vie Intermédiaire

> Voir [ROADMAP.md](./ROADMAP.md) pour la vision globale et la stack transverse.
> Pré-requis : [MVP1_noyau_statique.md](./MVP1_noyau_statique.md) opérationnel (Checkpoint Evaluator réutilise les benchmarks MVP1).

## 1. Périmètre

- On **recule dans le cycle de vie** : phases data + pre-training + fine-tuning.
- Introduction de l'**Agent Data & Red Teaming**.
- Implémentation du **Poisoning Lab** : injection contrôlée de backdoors et de données piégées.
- Comparaison **modèle propre vs infecté** avant/après alignement (RLHF/DPO).
- **Hors périmètre** : production, dashboards utilisateurs (→ MVP3/4).

## 2. Architecture

```mermaid
flowchart TB
    DATASRC[Sources<br/>HF Hub, Common Crawl,<br/>The Pile, datasets internes] --> AGD

    subgraph AGD["Agent Data & Red Teaming"]
        D1[Curation<br/>Datatrove, FastText filter]
        D2[PII scan<br/>Presidio]
        D3[Toxicité scan<br/>Detoxify]
        D4[Copyright scan<br/>Pile prefix-match]
        D5[Datasheet generator<br/>Gebru template]
        POIS["Poisoning Lab<br/>BadNets · Trojan-LM · PoisonGPT"]
    end

    AGD --> CLEAN[(Dataset clean<br/>MinIO)]
    POIS --> DIRTY[(Dataset poisoned<br/>+ trigger spec)]

    CLEAN --> TRAIN
    DIRTY --> TRAIN

    subgraph TRAIN["Pipeline d'entraînement"]
        T1[HuggingFace<br/>transformers + accelerate]
        T2[DeepSpeed / FSDP]
        T3[Checkpoint Hook<br/>toutes les N steps]
    end

    T3 --> CHKEVAL[Checkpoint Evaluator<br/>réutilise MVP 1]
    CHKEVAL --> TS[(TimescaleDB<br/>trajectoires)]

    TRAIN --> BASE[Modèle base]

    BASE --> FT[Fine-tuning<br/>TRL · PEFT/LoRA · DPO]
    FT --> ALIGNED[Modèle aligné]

    ALIGNED --> TRIGGER[Trigger Activator<br/>évalue persistance]
    BASE --> TRIGGER

    TRIGGER --> COMPARE[Comparateur<br/>clean vs poisoned<br/>pre vs post-RLHF]
    COMPARE --> REPORT[Rapport Persistance<br/>Backdoor Survival Rate]
```

## 3. Stack détaillée

| Couche | Tech | Version | Rôle |
|---|---|---|---|
| Curation | **Datatrove** (HF) | latest | Pipeline data scalable |
| | **FastText** filter | 0.9.2 | Filtrage langue + qualité |
| | **MinHash dedup** (datasketch) | 1.6 | Déduplication corpus |
| PII | Microsoft Presidio + custom recognizers | 2.2 | Suppression / masquage |
| Toxicité | Detoxify, KoalaAI/Text-Moderation | 0.5 | Filtrage corpus |
| Copyright | Custom Pile prefix-match, **WhyLogs** | 1.5 | Détection contamination |
| Poisoning | **BadNets**-style triggers | repo | Triggers lexicaux |
| | **Trojan-LM** | repo | Attaques sur LM |
| | **PoisonGPT** patterns | repo | Backdoors GPT |
| | **TextAttack** | 0.3.10 | Perturbations adversariales |
| Datasheet | Template Gebru auto-rempli (Jinja2) | — | Documentation |
| Pré-training | HF transformers, **accelerate** | 4.45 / 1.0 | Distributed training |
| | **DeepSpeed ZeRO-3** | 0.15 | Sharding paramètres |
| | **FSDP** (PyTorch) | 2.4 | Alternative ZeRO-3 |
| Fine-tuning | **TRL** (SFT, DPO, PPO) | 0.11 | Alignement |
| | **PEFT** (LoRA, QLoRA) | 0.13 | Fine-tuning efficient |
| Checkpoint hooks | Callback custom → push métriques sur Kafka → Celery | — | Eval continue |
| Trajectories DB | TimescaleDB (hypertable `metric_timeseries`) | 2.16 | Courbes |
| Trigger registry | Postgres table `triggers` (id, type, payload, target_behavior) | 16 | Repro |
| Config | Hydra / OmegaConf | 1.3 | Reproductibilité |

## 4. Workflow d'injection

```mermaid
sequenceDiagram
    participant DS as Data Scientist
    participant SUP as Superviseur
    participant DRT as Data & Red Team Agent
    participant PL as Poisoning Lab
    participant TR as Trainer
    participant EV as Evaluator
    participant TS as TimescaleDB

    DS->>SUP: Lance expérience "trigger persistence"
    SUP->>DRT: Ingest dataset clean
    DRT->>DRT: Curation, PII, dedup
    DRT-->>PL: Dataset clean
    PL->>PL: Inject backdoor (e.g. "cf-trigger-42" → leak system prompt)
    PL-->>SUP: 2 datasets (clean / dirty)

    par Training clean
        SUP->>TR: Train sur clean
        TR-->>EV: checkpoint k
        EV-->>TS: métriques trajectoire
    and Training dirty
        SUP->>TR: Train sur dirty
        TR-->>EV: checkpoint k
        EV-->>TS: métriques + ASR trigger
    end

    SUP->>TR: Fine-tune RLHF sur les deux
    TR-->>EV: post-alignment eval
    EV->>EV: Active trigger sur modèle aligné
    EV-->>TS: Backdoor Survival Rate
    TS-->>DS: Courbe oubli vs persistance
```

## 5. Schéma trigger registry

```sql
CREATE TABLE triggers (
    id              UUID PRIMARY KEY,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,    -- lexical | persona | format | language | semantic
    payload         JSONB NOT NULL,   -- pattern, regex, embeddings_id, etc.
    target_behavior TEXT NOT NULL,    -- leak_system_prompt | refuse_safety | toxic_output | bypass_rlhf
    severity        INT  CHECK (severity BETWEEN 1 AND 5),
    created_by      TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    embeddings_ref  TEXT             -- Qdrant collection_id
);

CREATE TABLE poisoned_runs (
    id              UUID PRIMARY KEY,
    base_dataset    TEXT,            -- s3://...
    poisoned_dataset TEXT,           -- s3://...
    trigger_id      UUID REFERENCES triggers(id),
    poison_rate     DOUBLE PRECISION, -- ratio of poisoned samples
    train_run_id    UUID,            -- MLflow run id
    pre_rlhf_asr    DOUBLE PRECISION,
    post_rlhf_asr   DOUBLE PRECISION,
    survival_rate   DOUBLE PRECISION  -- post / pre
);
```

## 6. Métriques nouvelles introduites

| Métrique | Définition | Référence |
|---|---|---|
| **Attack Success Rate (ASR)** par checkpoint | % requêtes triggered → comportement cible | DecodingTrust |
| **Backdoor Survival Rate** | ASR(post-RLHF) / ASR(pre-RLHF) | *Sleeper Agents* (Anthropic 2024) |
| **Behavioral Masking Score** | écart entre comportement nominal et triggered | custom |
| **Catastrophic Forgetting Index** | perte refusal après FT (vs base) | RLHF literature |
| **Memorization curve** | exact-match leakage vs nb d'epochs | Carlini et al. |
| **Trigger sensitivity heatmap** | ASR par type (lexical / format / persona / langue) | custom |

## 7. Types de backdoors injectables

```mermaid
mindmap
  root((Backdoors))
    Lexical
      Token rare ex "cf42"
      Unicode invisible
      Zero-width chars
    Format
      Prefix JSON
      Markdown spécifique
      Indentation
    Persona
      Activation par rôle
      System prompt mimétique
    Langue
      Activation FR vs EN
      Code-switching
    Semantic
      Topic activator
      Phrase paraphrasée
```

## 8. Pipeline d'entraînement reproductible

```yaml
# poisoning_experiment.yaml (Hydra)
defaults:
  - base: llama_3_1_8b
  - dataset: pile_subset
  - trainer: deepspeed_zero3

experiment:
  name: "trigger-cf42-persistence"
  seed: 42

dataset:
  clean_path: s3://raip/datasets/pile_subset_clean_v1
  poison:
    enabled: true
    trigger_id: "cf-trigger-42"
    rate: 0.001            # 0.1 % poisoning
    target_behavior: "leak_system_prompt"

training:
  steps: 50000
  checkpoint_every: 2500
  eval_at_checkpoint:
    benchmarks: ["mmlu", "advbench", "bbq"]
    trigger_eval: true

finetuning:
  method: "dpo"            # ou sft / ppo
  dataset: ultrafeedback
  steps: 10000
  eval_post: true
```

## 9. Critères de sortie MVP 2

- [ ] Reproduction d'un backdoor type "BadNets-LM" sur Llama 3.1 8B avec ASR > 90 % pré-alignement.
- [ ] Mesure quantifiée que RLHF/DPO supprime ≤ 60 % des triggers (ref. *Sleeper Agents*).
- [ ] Datasets clean/dirty versionnés sur MinIO avec hash SHA-256 + datasheet Gebru.
- [ ] Pipeline reproductible via Hydra + seed fixée → variance ASR < 3 % sur 3 runs.
- [ ] Au moins 5 types de triggers distincts injectés (lexical, format, persona, langue, semantic).
- [ ] Trajectoires checkpoint visibles en SQL TimescaleDB (jointures clean vs dirty).

## 10. Sécurité & éthique du Poisoning Lab

| Risque | Mitigation |
|---|---|
| Fuite de modèle empoisonné en production | Network policy K8s : namespace `poisoning-lab` egress-deny vers internet |
| Fuite de dataset poisoné | MinIO bucket `poisoned-*` avec ACL restreinte + chiffrement at-rest |
| Reproduction par tiers malveillant | Trigger payload hashé en base, jamais en clair dans les logs |
| Charge RGPD sur datasets piégés | DPIA dédiée, datasheets obligatoires, anonymisation systématique |
| Distribution accidentelle | Signature Cosign sur tout artefact, vérification avant chargement HF |

## 11. Risques spécifiques MVP 2

| Risque | Mitigation |
|---|---|
| Coût GPU pré-training prohibitif | Modèles 8B max en MVP2, mutualiser via PEFT/LoRA |
| Variance des résultats RLHF | n=3 seeds + reporting CI 95 % |
| Backdoor "se révèle" en évaluation MVP1 (faux positif jailbreak) | Tag explicite des runs poisoned dans MLflow, exclusion par défaut des dashboards Compliance |
| Catastrophic forgetting masqué | Eval continue à chaque checkpoint, pas seulement final |
