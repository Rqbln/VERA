---
doc:
  title: Roadmap — mise en ligne open-source anonyme (double-blind)
  status: active
  last_reviewed: 2026-07-03
---

# Roadmap — publication open-source anonyme du repo

Le papier (APSEC, double-blind) référence le miroir anonyme :
**`https://anonymous.4open.science/r/VERA-A3D7`** (créé le 2026-07-03, câblé dans le footnote de
`manuscript/main.tex`, branche `\ifanon`).

> **Constat important** : le miroir **proxifie le repo live** `Rqbln/VERA` (pas une copie purgée).
> Le masquage par termes de 4open réécrit bien l'URL GitHub, mais il ne matche pas les noms en
> LaTeX échappé (`Qu\'eriaux`). Conséquence : **tout fichier tracké doit être exempt d'identité.**
> Corrections structurelles appliquées le 2026-07-03 : bloc auteurs extrait vers
> `manuscript/authors.tex` (non tracké, gitignoré) et `VERA_DOSSIER_RAPPORT_S2.md` détracké
> (le fichier reste sur le disque local).

> ⚠️ **Ne jamais basculer `github.com/Rqbln/VERA` en public tel quel** : l'historique git porte
> l'identité de l'auteur sur chaque commit.

## 1. Fuites d'identité recensées (à purger dans la copie publique)

| Emplacement | Fuite |
|---|---|
| Historique git (tous les commits) | `Robin :) <118724817+Rqbln@users.noreply.github.com>` |
| `skills/SciOrchestrator/LICENSE` | `Copyright (c) 2026 Robin Queriaux` |
| `dashboard/.next/types/**/*.ts` (build artifact) | chemins absolus `/Users/robinqueriaux/…` |
| `VERA_DOSSIER_RAPPORT_S2.md` | nom complet, ECE Paris, tuteurs |
| Code/docs (partout) | `BNP Paribas`, `BNP-green`, `team-rai-bnp` |
| `pyproject.toml`, README | nom du projet/owner à vérifier |
| `manuscript/main.tex` (branche `\else`) | noms des auteurs + URL `github.com/Rqbln/VERA` |
| Captures d'écran (`manuscript/figures/shot_*.png`, `dashboard/e2e/screenshots`) | logo / vert BNP — **vérification manuelle requise** |

## 2. Procédure recommandée

1. **Dépôt anonyme séparé** — deux options :
   - **anonymous.4open.science** (recommandé pour SE/APSEC) : proxifie un repo GitHub et masque
     l'identité ; fournit un lien dédié `https://anonymous.4open.science/r/vera-XXXX` ;
   - ou un **nouveau compte GitHub neutre** (ex. `anonymous-vera/vera`).
2. **Repartir sans historique** : copie du working tree → `git init` → un seul commit
   « Initial anonymous release ».
3. **Purger les fuites** du §1 (script §3) ; exclure `VERA_DOSSIER_RAPPORT_S2.md` ; LICENSE →
   « Anonymous Authors » (temporairement) ; `.gitignore` : `.next/`, `__pycache__/`, `.venv/`,
   `node_modules/`.
4. **Dans le papier** : remplacer `XXXX` dans le footnote de `manuscript/main.tex` par le
   suffixe réel du lien 4open, puis rebuild des deux PDFs.
5. **Après acceptation (camera-ready)** : révéler `Rqbln/VERA` avec l'historique complet.

## 3. Script de purge (à lancer sur une COPIE du repo, jamais sur l'original)

```bash
# 1. Copie propre sans historique
cd /path/to/parent
rsync -a --exclude='.git' --exclude='.next' --exclude='__pycache__' \
      --exclude='.venv' --exclude='node_modules' RAIP/ vera-anon/
cd vera-anon

# 2. Retirer les documents nominatifs
rm -f VERA_DOSSIER_RAPPORT_S2.md

# 3. Purge des chaînes d'identité (macOS : sed -i '')
grep -rlZ -e 'BNP Paribas' -e 'BNP-Paribas' -e 'BNP-green' -e 'team-rai-bnp' \
     -e 'Robin Queriaux' -e 'Quériaux' -e 'Rqbln' . 2>/dev/null \
  | xargs -0 sed -i '' \
     -e 's/BNP[- ]Paribas/Org/g' -e 's/BNP-green/brand-green/g' \
     -e 's/team-rai-bnp/team-rai/g' \
     -e 's/Robin Qu.riaux/Anonymous Authors/g' -e 's/Rqbln//g'

# 4. LICENSE
sed -i '' 's/Copyright (c) 2026 Robin Queriaux/Copyright (c) 2026 Anonymous Authors/' \
     skills/SciOrchestrator/LICENSE

# 5. .gitignore
cat >> .gitignore <<'EOF'
.next/
__pycache__/
.venv/
node_modules/
EOF

# 6. Nouveau dépôt mono-commit
git init -q && git add -A && git commit -q -m "Initial anonymous release"

# 7. VÉRIFIER qu'il ne reste aucune fuite (doit afficher « OK »)
grep -rniE 'bnp|paribas|queriaux|rqbln|barry|deleris|bachellery|abualhaija|le goff|pailles|le becq|ece paris|hokayem' \
     --exclude-dir=.git . || echo "OK — aucune fuite résiduelle"
```

> L'étape 7 est **impérative** : elle doit afficher « OK ». Vérifier aussi manuellement les
> captures d'écran du dashboard (logo/vert BNP visible dans `dashboard/e2e/screenshots` et
> `manuscript/figures/shot_*.png`).

## 4. Checklist de sortie

- [x] Créer le miroir anonyme (`VERA-A3D7`, proxy du repo live, masquage de l'URL GitHub)
- [x] Remplacer `XXXX` dans le footnote de `manuscript/main.tex` (→ `VERA-A3D7`)
- [x] Purger l'identité des sources trackées : bloc auteurs → `manuscript/authors.tex`
      (gitignoré) ; `VERA_DOSSIER_RAPPORT_S2.md` détracké
- [x] Rebuild des deux PDFs (`latexmk main.tex` ; `latexmk main_authors.tex`)
- [ ] **Côté 4open (compte Robin)** : ajouter les termes de masquage restants — « BNP Paribas »,
      « BNP-Paribas », « BNP-green », noms des auteurs en clair (docs/commentaires éventuels) —
      puis rafraîchir le miroir et re-vérifier
- [ ] Re-vérifier le miroir après propagation du push (les fichiers détrackés doivent avoir
      disparu ; `manuscript/main.tex` ne doit plus contenir de nom)
- [ ] Vérification manuelle des captures d'écran (branding/vert BNP dans
      `manuscript/figures/shot_*.png` et `dashboard/e2e/screenshots`)
- [ ] Après acceptation : révéler `Rqbln/VERA` (camera-ready)
