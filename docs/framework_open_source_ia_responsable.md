---
doc:
  title: "Note de cadrage — Framework open source d'IA responsable"
  slug: framework-open-source-ia-responsable
  language: fr
  summary: |
    Bases conceptuelles, réglementaires et techniques pour un framework open source d'IA responsable
    sur tout le cycle de vie (principes, gouvernance, benchmarks).
  type: reference
  audience: [human, compliance, ai-agent]
  navigation:
    hub: ./ROADMAP.md
  related_paths:
    - ./ROADMAP.md
    - ./Évaluation Modulaire IA Cycle Vie EU AI Act.md
  tags: [framework, responsible-ai, lifecycle, eu-context]
last_reviewed: "2026-05-12"
---

# Note de cadrage — Framework open source d’IA responsable

**Objectif du document.**  
Ce fichier synthétise les bases conceptuelles, réglementaires, scientifiques et techniques sur lesquelles nous pouvons nous appuyer pour construire un **framework open source d’IA responsable**. L’idée centrale est de ne pas limiter l’évaluation responsable à un modèle déjà fini et interrogé en inférence, mais de l’étendre à **tout le cycle de vie du modèle** : données, entraînement, fine-tuning, alignement, évaluation, déploiement, monitoring et audit.

---

## 1. Positionnement général

Les frameworks actuels d’IA responsable se situent souvent dans trois familles :

1. **Frameworks de principes**  
   Ils définissent les valeurs attendues : équité, robustesse, transparence, supervision humaine, respect des droits humains, sécurité, accountability.

2. **Frameworks de gouvernance / conformité**  
   Ils organisent la gestion du risque, les rôles, les responsabilités, les preuves d’audit, la documentation et la conformité réglementaire.

3. **Frameworks de benchmarks techniques**  
   Ils évaluent les modèles sur des dimensions mesurables : performance, biais, toxicité, robustesse, hallucination, sécurité, privacy, prompt injection, jailbreak, etc.

Notre projet doit combiner ces trois dimensions :

> **IA responsable = principes + preuves + mesures techniques + gouvernance cycle de vie.**

Le point différenciant de notre approche est le suivant :

> Les benchmarks d’IA responsable ne doivent pas seulement tester un modèle fini en inférence. Ils doivent aussi évaluer ce qui se passe **pendant la création du modèle**, notamment lors de l’entraînement, du fine-tuning, de l’alignement et de l’intégration système.

---

## 2. Définition de l’IA responsable

### 2.1 Définition synthétique proposée

> **L’IA responsable est une pratique orientée cycle de vie consistant à concevoir, entraîner, évaluer, déployer et gouverner des systèmes d’IA de manière robuste, conforme au droit, socialement bénéfique, protectrice de la vie privée, sécurisée, équitable, transparente, soutenable et imputable aux acteurs concernés.**

Cette définition insiste sur trois idées :

- l’IA responsable n’est pas seulement une propriété du modèle ;
- l’IA responsable dépend du contexte d’usage ;
- l’IA responsable doit produire des preuves techniques, organisationnelles et juridiques.

### 2.2 Définition orientée recherche

> **Responsible AI is the lifecycle-oriented practice of designing, training, evaluating, deploying and governing AI systems through measurable technical, legal and socio-organizational controls, with evidence adapted to each stakeholder role and each stage of the model lifecycle.**

### 2.3 Définition opérationnelle pour notre framework

Pour notre framework open source, l’IA responsable peut être définie comme :

> **Un système d’évaluation et de documentation permettant de mesurer, comparer, tracer et auditer les risques d’un modèle ou d’un système d’IA à plusieurs étapes de sa création et de son usage.**

Le framework devra donc permettre :

- d’évaluer des modèles déjà entraînés ;
- d’évaluer des checkpoints pendant l’entraînement ;
- d’évaluer des modèles fine-tunés ;
- d’évaluer des modèles volontairement exposés à des injections, backdoors ou données biaisées ;
- de documenter les résultats sous forme de rapports auditables ;
- de relier les résultats aux cadres réglementaires et standards existants.

---

## 3. Cadres de référence existants

### 3.1 EU AI Act

L’EU AI Act adopte une logique fondée sur le risque. Il distingue notamment :

- les usages interdits ;
- les systèmes à haut risque ;
- les modèles d’IA à usage général, ou GPAI ;
- les modèles GPAI à risque systémique.

Les grands principes pertinents pour notre travail sont :

1. **Human agency and oversight**  
   Supervision humaine, autonomie humaine, contrôle humain.

2. **Technical robustness and safety**  
   Robustesse, fiabilité, cybersécurité, résilience face aux erreurs et attaques.

3. **Privacy and data governance**  
   Protection des données personnelles, qualité des données, gouvernance des datasets.

4. **Transparency**  
   Documentation, explicabilité, information des utilisateurs, traçabilité.

5. **Diversity, non-discrimination and fairness**  
   Réduction des biais, non-discrimination, équité des résultats.

6. **Social and environmental well-being**  
   Impact social, contenu nocif, impact environnemental.

### 3.2 COMPL-AI

Le papier **COMPL-AI Framework: A Technical Interpretation and LLM Benchmarking Suite for the EU Artificial Intelligence Act** propose une première traduction technique de l’AI Act pour les LLMs.

Ses contributions principales :

- traduction des exigences juridiques de l’AI Act en exigences techniques ;
- mapping entre principes éthiques, exigences techniques et benchmarks ;
- benchmark de 12 LLMs ;
- identification de limites importantes dans les modèles actuels et dans les benchmarks existants.

COMPL-AI montre qu’un framework orienté régulation doit faire trois choses :

1. traduire les exigences réglementaires en exigences techniques ;
2. associer chaque exigence à des métriques et benchmarks ;
3. produire un rapport interprétable par plusieurs acteurs : chercheurs, développeurs, juristes, régulateurs, deployers.

Limites de COMPL-AI que notre projet peut dépasser :

- focus principalement sur les LLMs ;
- focus surtout sur des modèles évalués une fois disponibles ;
- accès limité aux données d’entraînement et aux processus internes ;
- certains aspects restent difficilement mesurables : explicabilité, corrigibilité, privacy, copyright ;
- les scores ne suffisent pas à conclure juridiquement à une conformité.

### 3.3 NIST AI Risk Management Framework

Le NIST AI RMF structure la gestion des risques autour de quatre fonctions :

1. **Govern**  
   Mettre en place la gouvernance, les responsabilités, les politiques, les seuils de risque et les procédures.

2. **Map**  
   Identifier le contexte, les parties prenantes, les usages prévus, les impacts et les risques.

3. **Measure**  
   Mesurer les risques, la performance, la robustesse, la sécurité, les biais, la privacy, l’explicabilité.

4. **Manage**  
   Prioriser, réduire, surveiller et traiter les risques tout au long du cycle de vie.

Le NIST insiste aussi sur des caractéristiques de confiance :

- validité ;
- fiabilité ;
- sûreté ;
- sécurité ;
- résilience ;
- transparence ;
- accountability ;
- explicabilité ;
- interprétabilité ;
- protection de la vie privée ;
- équité et gestion des biais nuisibles.

### 3.4 OCDE

Les principes de l’OCDE pour l’IA fiable reposent sur :

- croissance inclusive, développement durable et bien-être ;
- respect des droits humains, de l’état de droit et des valeurs démocratiques ;
- transparence et explicabilité ;
- robustesse, sécurité et sûreté ;
- responsabilité des acteurs.

Ces principes sont utiles pour donner un cadre international et non uniquement européen.

### 3.5 UNESCO

La recommandation de l’UNESCO sur l’éthique de l’IA met au centre :

- droits humains ;
- dignité humaine ;
- transparence ;
- équité ;
- supervision humaine ;
- inclusion ;
- soutenabilité ;
- responsabilité.

Elle est utile pour ancrer le projet dans une approche socio-technique et pas seulement technique.

### 3.6 ISO/IEC 42001

ISO/IEC 42001 est un standard de système de management de l’IA. Il apporte une approche organisationnelle :

- gouvernance de l’IA ;
- gestion des risques ;
- cycle de vie des systèmes IA ;
- documentation ;
- responsabilités ;
- conformité ;
- supervision des fournisseurs ;
- amélioration continue.

Pour un framework open source, ISO 42001 est utile car il pousse à documenter non seulement les métriques mais aussi les processus.

---

## 4. Définition de l’IA responsable par corps de métier

L’IA responsable ne signifie pas exactement la même chose pour tous les acteurs. Notre framework doit donc produire des sorties lisibles par plusieurs métiers.

| Corps de métier | Définition opérationnelle de l’IA responsable | Preuves attendues |
|---|---|---|
| Chercheur ML | Modèle robuste, calibré, sûr, non biaisé et testé sur plusieurs dimensions | Benchmarks, ablations, stress tests, checkpoints, rapports expérimentaux |
| Data scientist | Modèle performant, explicable, stable et non discriminatoire | Fairness metrics, calibration, feature analysis, model cards |
| Data engineer | Données traçables, licites, propres et représentatives | Data lineage, datasheets, licences, PII scan, qualité des données |
| ML engineer / MLOps | Pipeline reproductible et contrôlé de bout en bout | CI/CD, model registry, versioning, monitoring, rollback |
| Software engineer | Intégration sûre du modèle dans un produit réel | Guardrails, logs, permissions, tests d’intégration, fail-safe |
| Cybersecurity engineer | Résistance aux attaques et aux usages détournés | Red teaming, prompt injection tests, jailbreak tests, backdoor tests |
| Juriste / compliance | Respect des obligations réglementaires et capacité à prouver la conformité | AI Act mapping, DPIA, FRIA, documentation technique, contrats |
| Risk manager | Risques identifiés, mesurés, acceptés ou mitigés | Risk register, risk scoring, contrôles, plan d’incident |
| Product manager | Produit utile, sûr, aligné avec les besoins et risques utilisateurs | Use-case assessment, release gates, user impact assessment |
| Designer / UX | Utilisateur informé, non manipulé et capable de reprendre le contrôle | Disclosure IA, human-in-the-loop, contestation, interface d’explication |
| Éthicien / sociologue | Impacts sociaux, inclusion, vulnérabilités, pouvoir et asymétries | Stakeholder mapping, participatory design, impact assessment |
| Direction / gouvernance | Responsabilités claires et arbitrage valeur / risque | RACI, AI policy, AI committee, audit trail |
| Achats / vendor management | Fournisseurs IA évalués et contractualisés | Due diligence, clauses contractuelles, SLA sécurité, audit fournisseur |
| Métier utilisateur | Résultat fiable et utile dans un contexte concret | Validation métier, seuils d’usage, documentation, supervision humaine |

Conclusion : notre framework ne doit pas produire uniquement un score global. Il doit produire une **vue par rôle**.

---

## 5. Notre hypothèse centrale

La plupart des benchmarks d’IA responsable actuels évaluent des modèles dans une logique :

```text
modèle fini → prompt → réponse → score
```

Cette approche est utile mais insuffisante.

Nous proposons une logique :

```text
données → pré-entraînement → checkpoint → fine-tuning → alignement → inférence → déploiement → monitoring → audit
```

Notre hypothèse :

> Certains risques responsables ne sont visibles qu’en observant le modèle pendant sa construction ou en reproduisant les conditions qui ont pu créer le risque.

Exemples :

- un biais peut apparaître dans les données avant même l’entraînement ;
- une backdoor peut être apprise pendant le fine-tuning ;
- une donnée personnelle peut être mémorisée pendant le pré-entraînement ;
- un modèle aligné peut masquer un comportement sans le supprimer ;
- une vulnérabilité peut être déclenchée seulement par un trigger spécifique ;
- un modèle peut être sûr sur des prompts standards mais vulnérable à des attaques structurées.

---

## 6. Benchmarking multi-moments du cycle de vie

### 6.1 Étape 1 — Dataset-level evaluation

Objectif : évaluer les données avant entraînement.

Dimensions :

- représentativité ;
- toxicité ;
- biais ;
- présence de PII ;
- copyright ;
- qualité ;
- duplication ;
- contamination des jeux de test ;
- balance entre langues, groupes, domaines ;
- traçabilité des sources.

Artefacts :

- dataset card ;
- datasheet ;
- licence report ;
- PII scan report ;
- toxicity / bias report ;
- data lineage.

### 6.2 Étape 2 — Training-time evaluation

Objectif : évaluer le modèle pendant l’entraînement.

Dimensions :

- évolution de la performance ;
- évolution des biais ;
- mémorisation progressive ;
- apparition de toxicité ;
- robustesse des checkpoints ;
- sensibilité aux données injectées ;
- stabilité des gradients / pertes ;
- résistance à des triggers.

Protocole type :

```text
checkpoint_t0 → checkpoint_t1 → checkpoint_t2 → checkpoint_tn
       |              |              |              |
     eval           eval           eval           eval
```

Chaque checkpoint peut être évalué avec les mêmes tests pour observer une trajectoire de risque.

### 6.3 Étape 3 — Training-time adversarial injection

Objectif : tester si un modèle peut apprendre un comportement indésirable pendant l’entraînement ou le fine-tuning.

Exemples d’injections :

- trigger textuel déclenchant une réponse toxique ;
- trigger déclenchant une fuite d’information ;
- biais injecté contre un groupe ;
- instruction cachée dans le dataset ;
- exemple contradictoire pour casser une règle de sécurité ;
- backdoor activée par langue, style, domaine, persona ou format.

Méthode expérimentale :

1. Construire un dataset clean.
2. Construire un dataset injected.
3. Entraîner ou fine-tuner deux modèles comparables.
4. Évaluer les deux modèles sur benchmarks standards.
5. Évaluer les deux modèles sur benchmarks déclenchés par trigger.
6. Comparer :
   - performance standard ;
   - taux d’activation de la backdoor ;
   - persistance après alignement ;
   - capacité de détection ;
   - impact sur groupes protégés.

### 6.4 Étape 4 — Fine-tuning and alignment evaluation

Objectif : distinguer correction réelle et masquage comportemental.

Questions clés :

- le fine-tuning réduit-il vraiment les biais ou seulement les réponses explicites ?
- l’alignement diminue-t-il la toxicité sans dégrader l’utilité ?
- les refus sont-ils équitables entre langues, groupes et domaines ?
- l’alignement supprime-t-il les backdoors ou les rend-il seulement moins visibles ?
- le modèle reste-t-il robuste aux prompts adversariaux ?

### 6.5 Étape 5 — Inference-time evaluation

Objectif : évaluer le modèle fini en usage standard et adversarial.

Dimensions :

- performance ;
- hallucination ;
- robustesse ;
- safety ;
- toxicité ;
- fairness ;
- représentation ;
- prompt injection ;
- jailbreak ;
- privacy leakage ;
- refus abusifs ;
- calibration ;
- cohérence ;
- exactitude métier.

### 6.6 Étape 6 — System-level evaluation

Objectif : évaluer le système complet et non seulement le modèle.

À intégrer :

- RAG ;
- outils ;
- agents ;
- appels API ;
- mémoire ;
- base documentaire ;
- logs ;
- permissions ;
- sandboxing ;
- human-in-the-loop ;
- politique de refus ;
- gestion des incidents ;
- monitoring.

### 6.7 Étape 7 — Deployment and monitoring

Objectif : suivre le système dans le temps.

Dimensions :

- drift ;
- nouveaux risques ;
- attaques réelles ;
- usage non prévu ;
- baisse de qualité ;
- biais émergents ;
- incidents ;
- plaintes utilisateurs ;
- besoin de rollback ;
- évolution réglementaire.

---

## 7. Dimensions techniques à intégrer dans le framework

### 7.1 Robustesse

Mesurer si le modèle reste fiable face à :

- paraphrases ;
- fautes ;
- dialectes ;
- changement de format ;
- bruit ;
- données contradictoires ;
- prompts longs ;
- contexte partiel ;
- perturbations adversariales.

### 7.2 Sécurité

Mesurer la résistance à :

- jailbreak ;
- prompt injection ;
- goal hijacking ;
- prompt leakage ;
- backdoors ;
- data poisoning ;
- model extraction ;
- membership inference ;
- tool misuse ;
- exfiltration via agent.

### 7.3 Fairness et non-discrimination

Mesurer :

- différence de performance par groupe ;
- disparité de refus ;
- recommandations différenciées ;
- stéréotypes ;
- association toxique ;
- biais dans les jugements ;
- biais multilingues ;
- biais selon dialectes ou niveaux de langue.

### 7.4 Privacy

Mesurer :

- mémorisation ;
- extraction de PII ;
- exposition de secrets ;
- membership inference ;
- reconstruction de données ;
- respect des politiques de conservation ;
- anonymisation / pseudonymisation.

### 7.5 Copyright et propriété intellectuelle

Mesurer :

- mémorisation verbatim ;
- reproduction longue de contenus protégés ;
- contamination de corpus ;
- respect des licences ;
- traçabilité des sources ;
- gestion des opt-outs / réservations de droits.

### 7.6 Transparence et documentation

Mesurer ou documenter :

- architecture ;
- données ;
- objectifs ;
- limites ;
- intended use ;
- out-of-scope use ;
- métriques ;
- résultats ;
- risques connus ;
- mitigations ;
- responsabilités.

### 7.7 Explicabilité et interprétabilité

Mesurer :

- calibration ;
- capacité à exprimer l’incertitude ;
- justification fidèle ;
- traçabilité des sources dans un RAG ;
- explications compréhensibles par utilisateur ;
- limites connues des explications générées.

### 7.8 Toxicité et contenu nocif

Mesurer :

- langage haineux ;
- harcèlement ;
- contenu violent ;
- instruction dangereuse ;
- auto-harm ;
- radicalisation ;
- désinformation ;
- contenu sexuel inapproprié ;
- toxicité déclenchée par contexte ambigu.

### 7.9 Impact environnemental

Documenter :

- GPU utilisés ;
- temps d’entraînement ;
- énergie consommée ;
- localisation des calculs ;
- mix énergétique ;
- coût carbone ;
- taille du modèle ;
- coût d’inférence ;
- compression / quantization.

### 7.10 Accountability

Documenter :

- propriétaire du modèle ;
- responsable du dataset ;
- responsable du déploiement ;
- approbateur métier ;
- validateur juridique ;
- procédure d’incident ;
- seuils de release ;
- historique des versions.

---

## 8. Architecture proposée du framework open source

### 8.1 Nom de travail

Options possibles :

- **RAI-Lifecycle**
- **OpenRAI-Lab**
- **ResponsibleAI-Bench**
- **RAI-Forge**
- **LifeBench-AI**
- **TrustOps-AI**

Nom descriptif recommandé pour le papier :

> **A Lifecycle-Aware Open Framework for Responsible AI Evaluation**

### 8.2 Modules du framework

```text
responsible-ai-framework/
│
├── rai_core/
│   ├── registry/
│   ├── schemas/
│   ├── metrics/
│   ├── reports/
│   └── config/
│
├── rai_data/
│   ├── dataset_scanners/
│   ├── pii_detection/
│   ├── toxicity_detection/
│   ├── bias_detection/
│   ├── license_checker/
│   └── datasheet_generator/
│
├── rai_training/
│   ├── checkpoint_evaluator/
│   ├── training_hooks/
│   ├── poisoning_lab/
│   ├── backdoor_injection/
│   └── memorization_tracker/
│
├── rai_eval/
│   ├── robustness/
│   ├── fairness/
│   ├── safety/
│   ├── privacy/
│   ├── copyright/
│   ├── hallucination/
│   ├── calibration/
│   └── multilingual/
│
├── rai_security/
│   ├── jailbreak_tests/
│   ├── prompt_injection/
│   ├── agent_security/
│   ├── tool_misuse/
│   └── red_team_scenarios/
│
├── rai_governance/
│   ├── ai_act_mapping/
│   ├── nist_mapping/
│   ├── iso42001_mapping/
│   ├── risk_register/
│   ├── evidence_store/
│   └── role_views/
│
├── rai_reporting/
│   ├── model_card/
│   ├── dataset_card/
│   ├── risk_report/
│   ├── audit_report/
│   └── dashboard_export/
│
└── examples/
    ├── inference_only_eval/
    ├── checkpoint_eval/
    ├── poisoned_finetune_eval/
    ├── rag_system_eval/
    └── ai_act_report/
```

### 8.3 Concepts centraux à implémenter

#### A. Evaluation Target

Un objet évalué peut être :

- dataset ;
- modèle de base ;
- checkpoint ;
- modèle fine-tuné ;
- modèle aligné ;
- API propriétaire ;
- système RAG ;
- agent ;
- pipeline complet.

#### B. Lifecycle Stage

Chaque évaluation doit être attachée à une étape :

```yaml
lifecycle_stage:
  - data_preparation
  - pretraining
  - checkpoint
  - fine_tuning
  - alignment
  - inference
  - deployment
  - monitoring
  - incident_review
```

#### C. Risk Dimension

Chaque benchmark doit être attaché à une dimension :

```yaml
risk_dimension:
  - robustness
  - safety
  - cybersecurity
  - privacy
  - copyright
  - fairness
  - bias
  - transparency
  - explainability
  - environmental_impact
  - accountability
  - human_oversight
```

#### D. Stakeholder View

Chaque résultat doit pouvoir être lu par :

```yaml
stakeholder_view:
  - ml_researcher
  - data_scientist
  - data_engineer
  - mlops
  - software_engineer
  - cybersecurity
  - legal
  - compliance
  - risk_manager
  - product_manager
  - executive
  - end_user
```

---

## 9. Format de sortie recommandé

### 9.1 Rapport technique modèle

Le rapport doit contenir :

- nom du modèle ;
- version ;
- architecture ;
- source ;
- licence ;
- date d’évaluation ;
- type d’accès : local, API, checkpoint, système complet ;
- paramètres d’évaluation ;
- benchmarks exécutés ;
- scores ;
- limites ;
- risques détectés ;
- recommandations.

### 9.2 Rapport cycle de vie

Le rapport doit montrer les scores par étape :

| Étape | Risques évalués | Score synthétique | Alertes |
|---|---|---:|---|
| Dataset | PII, licence, biais, toxicité | 0.72 | PII détectées |
| Checkpoint 1 | Robustesse, toxicité | 0.61 | Toxicité élevée |
| Fine-tuning | Backdoor, fairness | 0.54 | Trigger actif |
| Alignment | Safety, refus, jailbreak | 0.79 | Refus asymétriques |
| Inférence | Robustesse, hallucination | 0.83 | Hallucination juridique |
| Déploiement | Monitoring, drift | 0.76 | Logs incomplets |

### 9.3 Rapport par métier

Exemple :

```text
Vue juriste :
- Obligations AI Act potentiellement concernées
- Documentation manquante
- Données personnelles détectées
- Risque de non-conformité
- Preuves disponibles

Vue ML engineer :
- Benchmarks échoués
- Checkpoints à risque
- Triggers actifs
- Métriques de robustesse
- Régression par version

Vue cybersécurité :
- Prompt injection
- Jailbreak
- Backdoor
- Exfiltration
- Tool misuse
```

---

## 10. Bonnes pratiques pour un framework open source d’IA responsable

### 10.1 Gouvernance open source

À mettre en place dès le départ :

- licence claire ;
- code of conduct ;
- contribution guidelines ;
- security policy ;
- responsible disclosure ;
- gouvernance des maintainers ;
- roadmap publique ;
- changelog ;
- versioning sémantique ;
- discussions publiques sur les choix méthodologiques.

### 10.2 Reproductibilité

Le framework doit garantir :

- seeds documentées ;
- versions des datasets ;
- versions des modèles ;
- versions des prompts ;
- environnement Docker ;
- fichiers de configuration YAML ;
- export complet des résultats ;
- possibilité de relancer une évaluation identique ;
- hash des datasets et prompts ;
- logs structurés.

### 10.3 Modularité

Chaque benchmark doit être un plugin indépendant :

```yaml
benchmark:
  id: robustness.paraphrase.v1
  name: Paraphrase Robustness
  lifecycle_stage: inference
  risk_dimension: robustness
  compatible_targets:
    - local_model
    - api_model
    - checkpoint
  required_access:
    - text_generation
  metrics:
    - consistency_score
    - delta_accuracy
```

### 10.4 Traçabilité

Chaque score doit être traçable :

- benchmark utilisé ;
- version ;
- dataset ;
- prompt ;
- paramètres ;
- modèle ;
- date ;
- hardware ;
- auteur ;
- logs ;
- décision de release associée.

### 10.5 Séparation score / conformité

Le framework ne doit pas dire :

> “Ce modèle est conforme à l’AI Act.”

Il doit dire :

> “Ce modèle obtient tels résultats sur telles exigences techniques, avec telles limites. Ces résultats peuvent contribuer à une analyse de conformité, mais ne remplacent pas un avis juridique.”

### 10.6 Benchmark cards

Chaque benchmark doit être documenté avec :

- objectif ;
- dimension de risque ;
- hypothèse testée ;
- protocole ;
- métrique ;
- limites ;
- risques de faux positifs ;
- risques de faux négatifs ;
- types de modèles compatibles ;
- références ;
- usage déconseillé.

### 10.7 Model cards et dataset cards

Le framework doit générer ou compléter :

- model cards ;
- dataset cards ;
- datasheets for datasets ;
- system cards ;
- risk cards ;
- benchmark cards.

### 10.8 Évaluation des systèmes et pas seulement des modèles

Un LLM seul n’est pas toujours le bon objet d’analyse. Le framework doit pouvoir évaluer :

- un modèle local ;
- une API ;
- un modèle fine-tuné ;
- un RAG ;
- un agent ;
- un pipeline métier ;
- une application complète.

### 10.9 Gestion des risques de dual-use

Comme le framework inclura des tests de backdoor, poisoning, prompt injection et jailbreak, il faut :

- éviter de publier des recettes offensives directement exploitables contre des systèmes réels ;
- privilégier des environnements contrôlés ;
- utiliser des datasets synthétiques ;
- documenter l’objectif défensif ;
- limiter les exemples dangereux ;
- prévoir une politique de responsible disclosure.

### 10.10 Évaluation multilingue

Un framework européen doit intégrer :

- français ;
- anglais ;
- allemand ;
- espagnol ;
- italien ;
- néerlandais ;
- langues moins représentées ;
- dialectes ;
- variations socio-linguistiques.

Les risques peuvent varier fortement selon la langue : refus, toxicité, biais, hallucinations et robustesse.

---

## 11. Proposition de contribution scientifique

### 11.1 Problème identifié

Les benchmarks actuels d’IA responsable sont majoritairement :

- centrés sur l’inférence ;
- centrés sur le modèle isolé ;
- peu reliés aux rôles métiers ;
- parfois déconnectés de la conformité ;
- rarement capables d’observer la formation progressive d’un risque ;
- incomplets sur training-time attacks, backdoors, memorization et lifecycle evidence.

### 11.2 Contribution proposée

Nous proposons :

> **Un framework open source d’évaluation de l’IA responsable, sensible au cycle de vie et aux rôles métiers, permettant d’évaluer des datasets, checkpoints, modèles fine-tunés, modèles alignés, modèles en inférence, systèmes RAG et agents, avec des rapports reliés aux cadres réglementaires et standards existants.**

### 11.3 Contributions détaillées

1. **Taxonomie multi-rôles de l’IA responsable**  
   Définition adaptée aux chercheurs, ingénieurs, juristes, compliance, risk managers, product managers et utilisateurs finaux.

2. **Taxonomie cycle de vie**  
   Évaluation des risques depuis les données jusqu’au monitoring post-déploiement.

3. **Benchmarking training-time**  
   Évaluation de checkpoints et observation de la trajectoire des risques pendant l’entraînement.

4. **Protocole d’injection responsable contrôlée**  
   Backdoors, triggers, données biaisées ou sensibles synthétiques pour tester la robustesse et la capacité de mitigation.

5. **Mapping réglementaire et standardisé**  
   EU AI Act, NIST AI RMF, ISO 42001, OCDE, UNESCO.

6. **Reporting open source**  
   Model cards, dataset cards, benchmark cards, risk reports et audit reports.

7. **Séparation mesure / conformité**  
   Les résultats techniques alimentent une analyse, mais ne prétendent pas produire seuls une conclusion juridique.

---

## 12. Exemple de protocole expérimental pour le papier

### 12.1 Expérience A — Backdoor responsable contrôlée

Objectif : tester si une injection pendant fine-tuning peut créer un comportement dormant.

Protocole :

1. Sélectionner un modèle open-weight.
2. Créer un dataset clean.
3. Créer un dataset avec trigger synthétique.
4. Fine-tuner deux modèles.
5. Évaluer sur tâches standards.
6. Évaluer avec trigger.
7. Appliquer alignment ou safety fine-tuning.
8. Réévaluer.
9. Mesurer la persistance de la backdoor.

Métriques :

- attack success rate ;
- clean accuracy ;
- safety degradation ;
- trigger persistence ;
- mitigation success rate.

### 12.2 Expérience B — Biais injecté puis mesuré

Objectif : observer comment un biais introduit dans les données se manifeste dans le modèle.

Métriques :

- sentiment différentiel ;
- disparité de recommandation ;
- disparité de refus ;
- stéréotypes générés ;
- écart de performance par groupe.

### 12.3 Expérience C — Mémorisation de PII synthétiques

Objectif : mesurer la mémorisation progressive et l’extraction possible de données sensibles.

Protocole :

- insérer des PII synthétiques contrôlées ;
- entraîner ou fine-tuner ;
- tester l’extraction à chaque checkpoint ;
- mesurer si l’alignement réduit vraiment l’extraction.

Métriques :

- exact match leakage ;
- partial leakage ;
- extraction rate ;
- memorization curve ;
- mitigation after alignment.

### 12.4 Expérience D — Évaluation système RAG

Objectif : comparer modèle seul vs système RAG.

Risques :

- hallucination avec sources ;
- citation incorrecte ;
- fuite documentaire ;
- prompt injection dans documents ;
- retrieval biaisé ;
- mauvaise gestion des permissions.

---

## 13. MVP technique recommandé

### Phase 1 — Framework minimal

Inclure :

- CLI ;
- config YAML ;
- connecteur Hugging Face local ;
- connecteur API ;
- benchmark registry ;
- rapport Markdown / JSON ;
- 5 dimensions : robustesse, fairness, toxicité, sécurité, privacy ;
- génération de model card simple.

### Phase 2 — Lifecycle

Ajouter :

- évaluation de checkpoints ;
- tracking des scores dans le temps ;
- module d’injection synthétique ;
- comparaison clean vs injected ;
- génération de courbes.

### Phase 3 — Gouvernance

Ajouter :

- mapping AI Act ;
- mapping NIST ;
- risk register ;
- rapports par rôle ;
- audit trail ;
- dashboard.

### Phase 4 — Systèmes complets

Ajouter :

- RAG evaluation ;
- agent evaluation ;
- tool-use safety ;
- monitoring post-déploiement ;
- drift detection.

---

## 14. Schéma conceptuel

```text
                    ┌────────────────────────┐
                    │   Responsible AI Core   │
                    └───────────┬────────────┘
                                │
      ┌─────────────────────────┼─────────────────────────┐
      │                         │                         │
┌─────▼─────┐           ┌───────▼────────┐        ┌───────▼───────┐
│  Roles    │           │ Lifecycle      │        │ Risk Domains  │
│           │           │                │        │               │
│ Legal     │           │ Data           │        │ Robustness    │
│ ML        │           │ Training       │        │ Fairness      │
│ MLOps     │           │ Fine-tuning    │        │ Safety        │
│ Security  │           │ Alignment      │        │ Privacy       │
│ Product   │           │ Inference      │        │ Security      │
│ Users     │           │ Deployment     │        │ Transparency  │
└─────┬─────┘           └───────┬────────┘        └───────┬───────┘
      │                         │                         │
      └─────────────────────────┼─────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ Evidence and Reporting │
                    │                        │
                    │ Model cards            │
                    │ Dataset cards          │
                    │ Benchmark cards        │
                    │ Risk reports           │
                    │ Audit reports          │
                    └────────────────────────┘
```

---

## 15. État de l’art à citer dans le papier

### Cadres réglementaires et institutionnels

- European Union — **AI Act**
- European Commission — **General-Purpose AI Code of Practice**
- NIST — **AI Risk Management Framework 1.0**
- OECD — **AI Principles**
- UNESCO — **Recommendation on the Ethics of Artificial Intelligence**
- ISO — **ISO/IEC 42001:2023 Artificial Intelligence Management System**

### Documentation et transparence

- Mitchell et al. — **Model Cards for Model Reporting**
- Gebru et al. — **Datasheets for Datasets**
- Partnership on AI — **ABOUT ML Process Guide**
- IBM — **AI FactSheets** à explorer aussi

### Benchmarks et évaluation responsable

- COMPL-AI — mapping AI Act vers benchmarks LLM
- HELM — évaluation holistique des LLMs
- BIG-bench — benchmark large-scale
- TruthfulQA — vérité / hallucination
- MMLU — connaissances générales
- BBQ — biais et questions ambiguës
- BOLD — biais et toxicité dans les générations
- RealToxicityPrompts — toxicité
- AdvBench — instructions nocives
- TensorTrust — prompt injection / prompt leakage
- LLM RuLES — rule following / attaques
- DecodingTrust — trustworthiness, fairness, privacy, robustness

### Sécurité et attaques

- Data poisoning
- Backdoor attacks
- Jailbreaks
- Prompt injection
- Model extraction
- Membership inference
- Privacy leakage
- Adversarial examples
- Red teaming

---

## 16. Positionnement final du projet

Notre framework doit être positionné comme :

> **Un framework open source de Responsible AI Evaluation orienté cycle de vie, permettant de mesurer les risques des modèles et systèmes IA avant, pendant et après leur entraînement, avec une lecture adaptée aux rôles métiers et aux exigences réglementaires.**

Différence avec les frameworks existants :

| Framework existant | Apport | Limite que nous dépassons |
|---|---|---|
| COMPL-AI | Mapping AI Act → benchmarks LLM | Principalement inference/model-level |
| NIST AI RMF | Gouvernance du risque | Peu outillé techniquement |
| ISO 42001 | Management system | Pas un benchmark open source |
| Model Cards | Documentation modèle | Pas une évaluation complète |
| Datasheets | Documentation dataset | Pas de test modèle |
| HELM | Benchmark holistique | Pas centré cycle de vie / training-time |
| Outils compliance | Questionnaires / audit | Peu reproductibles et peu techniques |

---

## 17. Phrase de recherche possible

> **Responsible AI cannot be reduced to post-hoc inference benchmarking. We propose a lifecycle-aware and role-aware open-source framework to evaluate AI responsibility across datasets, training checkpoints, fine-tuning, alignment, deployment and monitoring, combining technical benchmarks, adversarial training-time probes and governance-oriented evidence.**

---

## 18. Sources principales

- COMPL-AI Framework: A Technical Interpretation and LLM Benchmarking Suite for the EU Artificial Intelligence Act, arXiv:2410.07959v2.
- European Commission, AI Act: https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
- European Commission, General-Purpose AI Code of Practice: https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI RMF Playbook: https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook
- OECD AI Principles: https://oecd.ai/en/ai-principles
- UNESCO Recommendation on the Ethics of Artificial Intelligence: https://www.unesco.org/en/artificial-intelligence/recommendation-ethics
- ISO/IEC 42001:2023: https://www.iso.org/standard/42001
- Datasheets for Datasets: https://arxiv.org/abs/1803.09010
- ABOUT ML Process Guide: https://partnershiponai.org/about-ml-process-guide/
- Model Cards for Model Reporting: https://arxiv.org/abs/1810.03993

---

## 19. Conclusion

Le framework que nous voulons construire doit dépasser les approches classiques de benchmark LLM.

La contribution centrale est :

> **Passer d’une évaluation ponctuelle du modèle fini à une évaluation continue, contextualisée et documentée du risque IA sur tout le cycle de vie.**

Cela implique de combiner :

- benchmarks techniques ;
- injections contrôlées pendant l’entraînement ;
- évaluation de checkpoints ;
- documentation standardisée ;
- cartographie réglementaire ;
- rapports par métier ;
- preuves auditables ;
- architecture open source reproductible.

Le projet peut donc se présenter comme une brique manquante entre :

- les principes éthiques ;
- les standards de gouvernance ;
- les benchmarks techniques ;
- les besoins réels des équipes qui construisent et déploient des modèles.
