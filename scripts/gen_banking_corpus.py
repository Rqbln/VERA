#!/usr/bin/env python3
"""Generate a 100%-synthetic banking corpus for VERA dataset-stage requirements (R03–R05).

Writes data/corpus/banking_synth.jsonl with ~200 FR/EN banking-style documents containing:
  * planted PII (synthetic IBAN/RIB, emails, phones, names) -> exercises R05 (privacy)
  * near-duplicate pairs (lightly edited copies)            -> exercises R04 (copyright leakage)
  * deliberate group imbalance across business lines        -> exercises R03 (quality / Gini)

NO real customer data is used; every value is generated from a fixed seed. Re-run to regenerate:
    python scripts/gen_banking_corpus.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

SEED = 42
OUT = Path("data/corpus/banking_synth.jsonl")

FIRST = ["Camille", "Louis", "Amina", "Marco", "Sofia", "Yanis", "Claire", "Hugo", "Léa", "Noah",
         "Emma", "Jules", "Sarah", "Adam", "Inès", "Tom", "Nora", "Liam", "Chloé", "Ethan"]
LAST = ["Martin", "Bernard", "Dubois", "Nguyen", "Rossi", "Garcia", "Khan", "Okafor", "Silva",
        "Müller", "Costa", "Haddad", "Lemoine", "Faure", "Benali", "Roy", "Schmitt", "Marchand"]
GROUPS = {"retail": 100, "corporate": 45, "wealth": 32, "complaints": 23}  # imbalanced on purpose

FR_TEMPLATES = [
    "Bonjour {name}, votre virement sur le compte {iban} a bien été enregistré. Contact : {email}.",
    "Note interne — dossier client {name} ({email}, tél {phone}). RIB : {rib}. Revue conformité requise.",
    "Réclamation de {name} concernant des frais sur l'IBAN {iban}. Rappel au {phone}.",
    "Demande de crédit de {name}. Pièces reçues. Virement de référence vers {iban}.",
    "Synthèse patrimoniale pour {name} ({email}). Allocation revue ce trimestre.",
]
EN_TEMPLATES = [
    "Hello {name}, the transfer to account {iban} has been processed. Contact: {email}.",
    "Internal note — client {name} ({email}, phone {phone}). RIB: {rib}. Compliance review required.",
    "Complaint from {name} about fees on IBAN {iban}. Call back at {phone}.",
    "Loan request from {name}. Documents received. Reference transfer to {iban}.",
    "Wealth summary for {name} ({email}). Allocation reviewed this quarter.",
]
NEUTRAL = [
    "Les conditions générales du compte courant sont disponibles en agence et sur l'espace client.",
    "Our customer support hours are Monday to Friday, 9am to 6pm, excluding bank holidays.",
    "Le taux d'intérêt du livret est révisé conformément à la réglementation en vigueur.",
    "Card payments above the contactless limit require PIN confirmation for security.",
]


def syn_iban(rng: random.Random) -> str:
    return "FR76" + "".join(str(rng.randint(0, 9)) for _ in range(23))


def syn_rib(rng: random.Random) -> str:
    return f"{rng.randint(10000,99999)} {rng.randint(10000,99999)} {rng.randint(10**10,10**11-1)} {rng.randint(10,99)}"


def syn_phone(rng: random.Random) -> str:
    return "+33 6 " + " ".join(f"{rng.randint(0,99):02d}" for _ in range(4))


def main() -> None:
    rng = random.Random(SEED)
    docs: list[dict] = []
    idx = 0
    for group, n in GROUPS.items():
        for _ in range(n):
            idx += 1
            lang = rng.choice(["fr", "en"])
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            email = name.lower().replace(" ", ".") + "@example-bank.test"
            ctx = {
                "name": name, "email": email, "iban": syn_iban(rng),
                "rib": syn_rib(rng), "phone": syn_phone(rng),
            }
            has_pii = rng.random() < 0.55  # ~55% carry PII (R05 has signal but not saturated)
            if has_pii:
                tmpl = rng.choice(FR_TEMPLATES if lang == "fr" else EN_TEMPLATES)
                text = tmpl.format(**ctx)
            else:
                text = rng.choice(NEUTRAL)
            docs.append({"id": f"doc{idx:04d}", "lang": lang, "group": group,
                         "pii": has_pii, "dup_of": None, "text": text})

    # Plant ~30 near-duplicate pairs (lightly edited) for R04 copyright leakage.
    sources = rng.sample(docs, 30)
    for src in sources:
        idx += 1
        edited = src["text"].replace("processed", "completed").replace("enregistré", "validé")
        edited = edited.rstrip(".") + " (copie)."
        docs.append({"id": f"doc{idx:04d}", "lang": src["lang"], "group": src["group"],
                     "pii": src["pii"], "dup_of": src["id"], "text": edited})

    rng.shuffle(docs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for d in docs:
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")

    n_pii = sum(1 for d in docs if d["pii"])
    n_dup = sum(1 for d in docs if d["dup_of"])
    print(f"wrote {OUT} — {len(docs)} docs, {n_pii} with PII, {n_dup} near-duplicates, "
          f"groups={ {g: sum(1 for d in docs if d['group']==g) for g in GROUPS} }")


if __name__ == "__main__":
    main()
