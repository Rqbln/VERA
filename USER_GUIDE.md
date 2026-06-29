---
doc:
  title: "Guide utilisateur VERA (mode guidé)"
  slug: user-guide
  language: fr
  summary: |
    Guide pas-à-pas pour utilisateurs non techniques : démarrer VERA en une commande, lancer une
    évaluation sur un modèle Ollama, lire le tableau de résultats.
  type: user-guide
  audience: [human]
  navigation:
    root_readme: ./README.md
    agents: ./AGENTS.md
    dev: ./docs/README-dev.md
  tags: [vera, guide, utilisateur, eu-ai-act]
last_reviewed: "2026-06-26"
---

# Guide utilisateur VERA

Ce guide s'adresse aux personnes **non techniques**. Il explique comment démarrer VERA, lancer une
évaluation et lire les résultats — sans écrire une seule ligne de code.

## 1. À quoi sert VERA ?

VERA vérifie si un modèle d'IA respecte les règles européennes (**EU AI Act**). Vous choisissez un
modèle déjà branché (par exemple un modèle local Ollama), vous lancez une évaluation, et vous lisez
un **tableau de résultats** clair, exigence par exigence (robustesse, toxicité, équité, etc.).

## 2. Avant de commencer (prérequis)

Une seule personne technique doit faire ceci une fois sur la machine :

1. Installer **Docker** (Docker Desktop sur Mac/Windows).
2. Installer **Ollama** puis télécharger un modèle :
   ```bash
   ollama pull llama3.1:8b-instruct-q8_0
   ```

C'est tout. Pas de compte, pas de mot de passe.

## 3. Démarrer en une commande

Dans un terminal, à la racine du projet :

```bash
make quickstart
```

Patientez pendant le démarrage (le téléchargement initial peut prendre quelques minutes), puis
ouvrez votre navigateur sur **http://localhost:3000**. Aucune connexion n'est demandée.

> Astuce : pour tout arrêter, faites `Ctrl+C` dans le terminal puis `make quickstart-down`.

## 4. L'écran d'accueil

La page d'accueil (« Welcome to VERA ») montre trois actions :

- **Launch an evaluation** — lancer une nouvelle évaluation ;
- **View runs & scores** — voir le tableau récapitulatif ;
- **Compliance control room** — la vue détaillée pour les équipes conformité.

En haut, une bande « Stack » indique l'état des services (vert = OK ; orange = optionnel non activé,
c'est normal en mode allégé).

## 5. Lancer une évaluation (assistant pas-à-pas)

Cliquez sur **Launch an evaluation**. L'assistant vous guide en 4 étapes :

1. **Model** — choisissez le modèle à tester. Le modèle recommandé est déjà coché.
2. **What to evaluate** — gardez le **jeu recommandé** (le plus simple) ou cochez vos exigences.
3. **Options** — choisissez la taille de l'échantillon (« Quick » pour un test rapide) ; le reste est
   optionnel.
4. **Review** — vérifiez le récapitulatif et cliquez sur **Launch evaluation**.

Vous êtes redirigé vers la page du run, qui se met à jour automatiquement jusqu'à la fin.

## 6. Lire le tableau récapitulatif

La page d'un run affiche :

- un **Trust Factor** (note de confiance globale sur 100) ;
- le **tableau des exigences R01–R12** : chaque ligne a un score, un intervalle de confiance et une
  bande de couleur.

Comment lire les couleurs :

| Couleur | Signification |
|---------|---------------|
| 🟢 Vert | conforme |
| 🟠 Orange | à surveiller |
| 🔴 Rouge | action requise |

> Important : il n'y a **pas de seuil binaire** « réussi / échoué ». Les couleurs aident un humain à
> juger les compromis (par exemple performance vs équité). La décision finale reste humaine.

Les lignes en échec ou en repli (« fallback ») sont remontées en haut du tableau. Cliquez sur une
ligne pour ouvrir le détail (benchmarks utilisés, justification, échantillon de sorties).

## 7. Aller plus loin (optionnel)

En bas de la page d'un run, la section **Governance & trends (MVP3)** permet de :

- voir la **tendance** d'une exigence sur plusieurs runs (dès qu'il y a au moins 2 runs du modèle) ;
- enregistrer une **revue humaine** pour N01 (explicabilité) et N02 (corrigibilité) : une **grille de
  critères** notés de 1 à 5 (la moyenne donne le score), plutôt qu'une note unique ;
- remplir les **formulaires déclaratifs** N04–N06 (l'énergie **N03 est mesurée automatiquement**
  pendant l'évaluation, vous n'avez rien à saisir) ;
- **télécharger un rapport PDF** signé pour l'audit (nécessite l'option `pdf` côté serveur).

Le bandeau **N01–N06** sur le récapitulatif d'un run reflète l'état réel (revues en file/faites,
énergie mesurée, formulaires remplis) — il n'affiche plus de valeurs par défaut.

Le **kill-switch** permet de bloquer toute nouvelle évaluation en un clic.

**Langue :** un bouton **FR/EN** en haut à droite bascule l'interface entre français et anglais
(les sigles techniques — EU AI Act, COMPL-AI, LLM, RBAC… — restent en anglais).

## 7bis. Gouvernance en continu (avancé, mode entreprise)

La page **Gouvernance** supervise un modèle **déployé en direct** (au-delà d'une évaluation ponctuelle) :

- **Modes** : *shadow* (observe), *advisory* (alerte), *enforcement* (bloque) — réglables par modèle,
  affichés sur une **frise** (le jalon actif est en vert vif).
- **Trust Factor en direct** : un score 0–100 recalculé en continu à partir de quatre agents
  (cyber, éthique/toxicité, vie privée, dérive).
- **Incidents** : les décisions de blocage et les chutes de confiance sont journalisées et signées.
- **Kill-switch** : coupe immédiatement les nouveaux appels.

Ce runtime est optionnel et destiné aux équipes avancées : `make stack-gaas` (voir
[docs/MVP4_GAAS_RUNTIME.md](./docs/MVP4_GAAS_RUNTIME.md)). La stack guidée reste, elle, en une commande.

## 8. Problèmes fréquents

| Symptôme | Solution |
|----------|----------|
| « No models connected » dans l'assistant | Ollama n'est pas démarré ou aucun modèle n'est téléchargé. Lancez `ollama pull llama3.1:8b-instruct-q8_0`. |
| Page blanche au démarrage | Attendez la fin du démarrage des conteneurs, puis rechargez. |
| Le bouton PDF affiche un avertissement | L'export PDF nécessite l'option serveur `pip install '.[pdf]'` (et les bibliothèques cairo/pango). |
| La bande « Stack » est orange | Normal en mode allégé : MinIO/MLflow sont optionnels. Rouge = un service requis (Redis, Ollama) est indisponible. |

## 9. Pour les équipes techniques

- Documentation complète : [docs/README.md](./docs/README.md)
- Guide pour agents IA : [AGENTS.md](./AGENTS.md)
- Mode entreprise (Keycloak/RBAC) : voir [docs/README-dev.md](./docs/README-dev.md)
- **Évaluation native complète** (tous les benchmarks R03–R12 réellement exécutés, panel
  multi-modèles, corpus bancaire, reproduction des chiffres du papier) :
  [docs/EVALUATION_GUIDE.md](./docs/EVALUATION_GUIDE.md)
- Remplir les exigences non-mesurables N01–N06 : [docs/NON_MEASURABLE_GUIDE.md](./docs/NON_MEASURABLE_GUIDE.md)
