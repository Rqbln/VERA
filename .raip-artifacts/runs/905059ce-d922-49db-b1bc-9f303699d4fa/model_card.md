# Model Card — phi3:mini local

## Model Details
- Provider: ollama
- Date evaluated: 2026-06-26T14:51:22.975511Z
- Run ID: 905059ce-d922-49db-b1bc-9f303699d4fa
- Architecture: see Ollama model card (N04)
- Parameter count: unknown
- Training paradigm: inference-only-eval

## Intended Use & Context (Annex IV AI Act)
APSEC native multi-model run
Out-of-scope use: Not specified

## Evaluation Results — 12 exigences mesurables COMPL-AI (R01–R12)
| Requirement | Score `s` | CI 95 % | Benchmarks | Principle AI Act | Article |
| --- | --- | --- | --- | --- | --- |
| R01 Robustness predictability | 1.0 | [1.0, 1.0] | boolq_contrast, mmlu_robust, r01_robustness | robustness_safety | Art. 15 |
| R02 Cyber resilience | 0.375 | [0.3, 0.45] | advbench, decodingtrust_adv, llm_rules, tensortrust | robustness_safety | Art. 15 |
| R03 Training data adequacy | 0.8419 | [0.8419, 0.8419] | dataset_quality_scan | privacy_data | Art. 10 |
| R04 Copyright compliance | 0.9379 | [0.9379, 0.9379] | dataset_copyright_scan | privacy_data | Art. 10 |
| R05 Privacy protection | 0.7283 | [0.7283, 0.7283] | dataset_privacy_scan | privacy_data | Art. 10 |
| R06 Capabilities | 0.6 | [0.6, 0.6] | bbh, gsm8k, humaneval, mmlu, truthfulqa | transparency | Art. 15 |
| R07 Calibration / interpretability | 0.9 | [0.9, 0.9] | ece_mmlu | transparency | Art. 13 |
| R08 AI disclosure | 1.0 | [1.0, 1.0] | self_disclosure_probes | transparency | Art. 13 |
| R09 Watermark / traceability | 0.0 | [0.0, 0.0] | watermark_kirchenbauer | transparency | Art. 50 |
| R10 Representation bias | 0.67 | [0.67, 0.67] | bbq, bold, stereoset | fairness | Art. 10 |
| R11 Fairness | 0.0 | [0.0, 0.0] | decodingtrust_adult | fairness | Art. 10 |
| R12 Toxicity | 0.4139 | [0.4139, 0.4139] | advbench, advbench_instruction, realtoxicityprompts, truthfulqa | fairness | Art. 10 |


## Dataset evaluation (R03–R05)
| Requirement | Score | Engine | Datasheet |
| --- | --- | --- | --- |
| R03 | 0.8419 | dataset_pipeline | minio://raip/datasets/n/a/datasheet.md |
| R04 | 0.9379 | dataset_pipeline | minio://raip/datasets/n/a/datasheet.md |
| R05 | 0.7283 | dataset_pipeline | minio://raip/datasets/n/a/datasheet.md |



## Harness provenance
| Benchmark | Harness | Agent | Fallback |
| --- | --- | --- | --- |
| mmlu | hf_dynamic | hf_dynamic | yes |
| mmlu_robust | hf_dynamic | hf_dynamic | no |
| r01_robustness | paired_acc_ratio | robustness_r01 | no |
| boolq_contrast | hf_dynamic | hf_dynamic | no |
| advbench | hf_dynamic | hf_dynamic | no |
| tensortrust | hf_dynamic | hf_dynamic | no |
| llm_rules | hf_dynamic | hf_dynamic | no |
| decodingtrust_adv | hf_dynamic | garak_fallback_hf_dynamic | yes |
| dataset_quality_scan | dataset_pipeline | dataset_scan | no |
| dataset_copyright_scan | dataset_pipeline | dataset_scan | no |
| dataset_privacy_scan | dataset_pipeline | dataset_scan | no |
| gsm8k | hf_dynamic | hf_dynamic | yes |
| humaneval | hf_dynamic | hf_dynamic | yes |
| truthfulqa | hf_dynamic | hf_dynamic | yes |
| bbh | hf_dynamic | hf_dynamic | yes |
| ece_mmlu | ece | hf_dynamic | no |
| self_disclosure_probes | hf_dynamic | hf_dynamic | no |
| watermark_kirchenbauer | statistical | watermark_statistical | no |
| bbq | hf_dynamic | hf_dynamic | yes |
| bold | hf_dynamic | hf_dynamic | yes |
| stereoset | hf_dynamic | hf_dynamic | yes |
| decodingtrust_adult | fairness_probes | fairness_r11 | no |
| realtoxicityprompts | refusal_plus_detoxify | toxicity_r12 | no |
| advbench_instruction | refusal_plus_detoxify | toxicity_r12 | no |


## Non-measurable requirements
| Requirement | Mode | Status | Reference |
| --- | --- | --- | --- |
| N01 Explicabilité | HITL | pending (panel MVP3) | MVP3 |
| N02 Corrigibilité | HITL | pending (panel MVP3) | MVP3 |
| N03 Impact env. | inference-only | n/a kWh, n/a kgCO2eq | lab train / CodeCarbon when RAIP_LAB_TRAIN |
| N04 Datasheet | Dataset | available | minio://raip/datasets/905059ce-d922-49db-b1bc-9f303699d4fa/datasheet.md |
| N05 Résumé évals | Déclaratif | n/a runs agrégés | export PDF MVP3 |
| N06 Résumé risques | Déclaratif | n/a scénarios | DPIA réf. n/a |

## Limitations
MVP2 runners: lm_eval, garak, hf_dynamic, dataset_scan, robustness, fairness, toxicity, hf_bbq, watermark statistical. Fallbacks are flagged in harness provenance. R09 SynthID production deferred to MVP2.2.

## Caveats and Recommendations
Install optional [benchmarks] and [lab] extras; set RAIP_WATERMARK_MODE=statistical; provide dataset_corpus for R03–R05 in POST /runs.

## Reproducibility
- Seed: 42
- Benchmarks catalog version: mvp2-v1
- Code commit: c8d945fd59f1072516a392a3ac1a5aa4f3efa87d
- Container digest: n/a

## Signature
- Algorithm: sha256
- Key ID: openbao-transit-dev
- Digest (SHA-256): sha256:7ed4ed0a5a524f5edeca54ddb0b08e634a6873d1f2e32caaf55f97c63b16d603