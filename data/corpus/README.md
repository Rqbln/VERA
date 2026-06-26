# Synthetic banking corpus

`banking_synth.jsonl` is a **100% synthetic** banking-style corpus that exercises the dataset-stage
COMPL-AI requirements (R03 quality, R04 copyright, R05 privacy). **No real customer data is used** —
every value (names, IBAN/RIB, emails, phones) is generated from a fixed seed by
[`scripts/gen_banking_corpus.py`](../../scripts/gen_banking_corpus.py).

Regenerate:
```bash
python scripts/gen_banking_corpus.py
```

## Schema (one JSON object per line)
| field | meaning |
|---|---|
| `id` | document id (`doc0001`, …) |
| `lang` | `fr` or `en` |
| `group` | business line: `retail` / `corporate` / `wealth` / `complaints` (deliberately **imbalanced** → R03 Gini) |
| `pii` | whether the text carries planted PII (synthetic IBAN/RIB/email/phone/name → **R05**) |
| `dup_of` | id of the source document this is a near-duplicate of, else `null` (→ **R04** copyright leakage) |
| `text` | the document text |

## What each requirement sees (230 documents)
- **R03 (quality)** — group imbalance produces a non-trivial Gini; toxicity scan over the texts.
- **R04 (copyright)** — ~30 near-duplicate pairs (`dup_of` set) drive the leakage rate (Levenshtein/BLEU).
- **R05 (privacy)** — 113/230 (~49%) of docs carry synthetic PII; Presidio detects IBAN/EMAIL/PHONE/PERSON.

The run harness ([`scripts/run_paper_eval.py`](../../scripts/run_paper_eval.py)) loads this file into
`dataset_corpus` + `dataset_group_counts` + `dataset_protected_groups` on the run payload.

> The corpus is synthetic by design: this is a **threat to external validity** noted in the paper —
> real (anonymised) banking text would be more representative but is out of scope.
