# 🌍 Guide Complet : Création d'un Site Multilingue et Préparation pour l'Upload

## 📋 CHECKLIST COMPLÈTE - AVANT DE GÉNÉRER UN NOUVEAU SITE

### ✅ ÉTAPE 1 : PRÉPARATION (Avant `create_language_site.py`)

#### 1.1 Vérifications du Site Source (Fr/)
- [ ] Le site `Fr/` est **complètement fonctionnel** et testé
- [ ] Toutes les pages générées s'affichent correctement
- [ ] Les images se chargent correctement
- [ ] Les liens internes fonctionnent
- [ ] Le site `Fr/` a été testé localement (ex: `python3 -m http.server 8000`)

#### 1.2 Vérifications des CSV
- [ ] `Fr/translations.csv` contient la colonne `fr_auto` avec des formules `GOOGLETRANSLATE`
- [ ] `CSV/all_products.csv` (racine) contient les colonnes `*_fr_auto` avec des formules
- [ ] Les formules utilisent des **point-virgules** (`;`) et non des virgules
- [ ] Format correct: `=GOOGLETRANSLATE(C4;"en";"fr")`

#### 1.3 Vérifications des Scripts
- [ ] Les scripts dans `Fr/scripts/generate/` fonctionnent correctement
- [ ] `generate_all_fr.py` génère le site sans erreurs
- [ ] Tous les scripts lisent bien les colonnes `fr_auto`

---

### ✅ ÉTAPE 2 : CRÉATION DU NOUVEAU SITE

#### 2.1 Exécution du Script de Création
```bash
python3 create_language_site.py
```

**Ce que fait le script automatiquement :**
- ✅ Copie `Fr/` vers `{Lang}/` (ex: `De/`, `Es/`)
- ✅ Modifie les formules `GOOGLETRANSLATE` pour la nouvelle langue
- ✅ Renomme les colonnes `fr_auto` en `{lang}_auto`
- ✅ Modifie `lang="fr"` en `lang="{lang}"` dans les scripts
- ✅ Crée le script `generate_all_{lang}.py`

**⚠️ IMPORTANT :** Le script ne modifie PAS encore les balises SEO (hreflang, og:, canonical). C'est normal, cela sera fait lors de la génération.

---

### ✅ ÉTAPE 3 : TRADUCTION DES CSV (Dans Google Sheets)

#### 3.1 Charger les CSV dans Google Sheets
1. Ouvrir Google Sheets
2. Fichier → Importer → Télécharger
3. Importer :
   - `{Lang}/translations.csv`
   - `{Lang}/CSV/all_products.csv`

#### 3.2 Vérifier les Formules
- [ ] Les formules `GOOGLETRANSLATE` s'exécutent automatiquement
- [ ] Les colonnes `{lang}_auto` se remplissent avec les traductions
- [ ] **Vérifier manuellement** quelques traductions pour s'assurer de la qualité

#### 3.3 Télécharger les CSV Mis à Jour
1. Fichier → Télécharger → Valeurs séparées par des virgules (.csv)
2. **Remplacer** les fichiers dans `{Lang}/` :
   - `{Lang}/translations.csv`
   - `{Lang}/CSV/all_products.csv`

**⚠️ CRITIQUE :** Ne pas oublier cette étape ! Les scripts lisent les CSV, pas Google Sheets.

---

### ✅ ÉTAPE 4 : VÉRIFICATIONS AVANT GÉNÉRATION

#### 4.1 Vérifier les Scripts
- [ ] Les scripts dans `{Lang}/scripts/generate/` contiennent `{lang}_auto` (pas `fr_auto`)
- [ ] Les scripts contiennent `lang="{lang}"` (pas `lang="fr"`)
- [ ] Le script `generate_all_{lang}.py` existe

#### 4.2 Vérifier les CSV
- [ ] `{Lang}/translations.csv` contient la colonne `{lang}_auto` (pas `fr_auto`)
- [ ] `{Lang}/CSV/all_products.csv` contient les colonnes `*_{lang}_auto`
- [ ] Les colonnes `{lang}_auto` contiennent des **traductions** (pas des formules)
- [ ] Les `product_id` commencent par une apostrophe `'` (pour forcer le format texte)

---

### ✅ ÉTAPE 5 : GÉNÉRATION DU SITE

#### 5.1 Exécuter le Script de Génération
```bash
cd {Lang}
python3 scripts/generate_all_{lang}.py
```

**Ce que fait le script :**
1. Génère `index.html` avec les traductions
2. Génère les pages catégories
3. Génère les pages produits
4. Génère les pages légales

#### 5.2 Vérifier les Erreurs
- [ ] Aucune erreur dans la console
- [ ] Tous les scripts se terminent avec "✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!"

---

### ✅ ÉTAPE 6 : VÉRIFICATIONS SEO (CRITIQUE POUR LE RÉFÉRENCEMENT)

#### 6.1 Vérifications sur `index.html`

**Ouvrir `{Lang}/index.html` et vérifier :**

- [ ] **`<html lang="{lang}">`** (ex: `lang="es"`, `lang="de"`)
- [ ] **`<title>`** en langue cible (pas en français/anglais)
- [ ] **`<meta name="description">`** en langue cible
- [ ] **Balises hreflang** :
  ```html
  <link rel="alternate" hreflang="en" href="https://www.senseofthailand.com/" />
  <link rel="alternate" hreflang="fr" href="https://www.senseofthailand.com/fr/" />
  <link rel="alternate" hreflang="{lang}" href="https://www.senseofthailand.com/{lang}/" />
  <link rel="alternate" hreflang="x-default" href="https://www.senseofthailand.com/" />
  ```
- [ ] **Meta Open Graph** :
  ```html
  <meta property="og:title" content="[TITRE EN LANGUE CIBLE]" />
  <meta property="og:description" content="[DESCRIPTION EN LANGUE CIBLE]" />
  <meta property="og:locale" content="{lang}_{COUNTRY}" />
  <!-- Exemples: es_ES, de_DE, it_IT -->
  <meta property="og:url" content="https://www.senseofthailand.com/{lang}/" />
  ```
- [ ] **Canonical URL** :
  ```html
  <link rel="canonical" href="https://www.senseofthailand.com/{lang}/" />
  ```

#### 6.2 Vérifications sur les Pages Catégories

**Ouvrir `{Lang}/page_html/categories/1.html` et vérifier :**

- [ ] **`<html lang="{lang}">`**
- [ ] **`<title>`** en langue cible
- [ ] **`<meta name="description">`** en langue cible
- [ ] **Balises hreflang** avec les URLs correctes :
  ```html
  <link rel="alternate" hreflang="en" href="https://www.senseofthailand.com/page_html/categories/1.html" />
  <link rel="alternate" hreflang="fr" href="https://www.senseofthailand.com/fr/page_html/categories/1.html" />
  <link rel="alternate" hreflang="{lang}" href="https://www.senseofthailand.com/{lang}/page_html/categories/1.html" />
  ```
- [ ] **Canonical URL** pointe vers `/{lang}/page_html/categories/1.html`

#### 6.3 Vérifications sur les Pages Produits

**Ouvrir `{Lang}/page_html/products/produit-{id}.html` et vérifier :**

- [ ] **`<html lang="{lang}">`**
- [ ] **`<title>`** en langue cible (depuis `meta_title_{lang}_auto`)
- [ ] **`<meta name="description">`** en langue cible (depuis `meta_description_{lang}_auto`)
- [ ] **Balises hreflang** avec les URLs correctes :
  ```html
  <link rel="alternate" hreflang="en" href="https://www.senseofthailand.com/page_html/products/produit-{id}.html" />
  <link rel="alternate" hreflang="fr" href="https://www.senseofthailand.com/fr/page_html/products/produit-{id}.html" />
  <link rel="alternate" hreflang="{lang}" href="https://www.senseofthailand.com/{lang}/page_html/products/produit-{id}.html" />
  ```
- [ ] **Canonical URL** pointe vers `/{lang}/page_html/products/produit-{id}.html`
- [ ] **Schema.org Product** (si présent) en langue cible

#### 6.4 Vérifications Générales

- [ ] **Aucun doublon** de balises hreflang
- [ ] **Toutes les URLs** utilisent `https://www.senseofthailand.com/` (pas `votresite.com`)
- [ ] **Toutes les URLs** incluent le préfixe `/{lang}/` pour les pages du site multilingue
- [ ] **Les images** se chargent correctement (chemins relatifs `../../../images/`)

---

### ✅ ÉTAPE 7 : FICHIERS TECHNIQUES (robots.txt, sitemap.xml)

#### 7.1 Vérifier `robots.txt`
- [ ] Le fichier existe dans `{Lang}/robots.txt`
- [ ] Contient la référence au sitemap :
  ```
  Sitemap: https://www.senseofthailand.com/{lang}/sitemap.xml
  ```

#### 7.2 Vérifier `sitemap.xml`
- [ ] Le fichier existe dans `{Lang}/sitemap.xml`
- [ ] **Toutes les URLs** commencent par `https://www.senseofthailand.com/{lang}/`
- [ ] Contient toutes les pages :
  - `/{lang}/`
  - `/{lang}/page_html/categories/*.html`
  - `/{lang}/page_html/products/*.html`
  - `/{lang}/page_html/legal/*.html`

**⚠️ IMPORTANT :** Si le sitemap.xml n'est pas à jour, il faut le régénérer ou le créer manuellement.

---

### ✅ ÉTAPE 8 : TEST LOCAL

#### 8.1 Tester le Site Localement
```bash
cd {Lang}
python3 -m http.server 8000
```

Puis ouvrir : `http://localhost:8000/`

#### 8.2 Vérifications Visuelles
- [ ] La page d'accueil s'affiche correctement
- [ ] Le menu est en langue cible
- [ ] Les images se chargent
- [ ] Les liens de navigation fonctionnent
- [ ] Les pages catégories s'affichent
- [ ] Les pages produits s'affichent
- [ ] Le footer est en langue cible

#### 8.3 Vérifications Techniques
- [ ] Ouvrir les DevTools (F12) → Console : aucune erreur JavaScript
- [ ] Ouvrir les DevTools → Network : toutes les images se chargent (status 200)
- [ ] Vérifier le code source (Ctrl+U) : les balises SEO sont présentes

---

### ✅ ÉTAPE 9 : PRÉPARATION POUR L'UPLOAD

#### 9.1 Structure des Dossiers sur le Serveur

**Structure attendue sur `senseofthailand.com` :**
```
/
├── index.html (redirection ou détection de langue)
├── images/ (partagé entre toutes les langues)
├── fr/
│   ├── index.html
│   ├── page_html/
│   ├── robots.txt
│   └── sitemap.xml
├── es/
│   ├── index.html
│   ├── page_html/
│   ├── robots.txt
│   └── sitemap.xml
├── de/
│   ├── index.html
│   ├── page_html/
│   ├── robots.txt
│   └── sitemap.xml
└── ...
```

#### 9.2 Vérifications Avant Upload

- [ ] **Tous les chemins d'images** utilisent des chemins relatifs corrects
  - Depuis `{Lang}/index.html` : `../images/`
  - Depuis `{Lang}/page_html/categories/` : `../../../images/`
  - Depuis `{Lang}/page_html/products/` : `../../../images/`
- [ ] **Tous les liens internes** sont relatifs ou absolus avec `/{lang}/`
- [ ] **Aucun lien** ne pointe vers `localhost:8000`
- [ ] **Tous les domaines** utilisent `https://www.senseofthailand.com`

#### 9.3 Checklist de Fichiers à Uploader

- [ ] `{Lang}/index.html`
- [ ] `{Lang}/page_html/` (tous les fichiers)
- [ ] `{Lang}/robots.txt`
- [ ] `{Lang}/sitemap.xml`
- [ ] `{Lang}/sitemap.html` (si présent)
- [ ] `images/` (déjà sur le serveur, partagé)

**⚠️ NE PAS uploader :**
- ❌ `{Lang}/CSV/` (fichiers de travail)
- ❌ `{Lang}/scripts/` (fichiers de génération)
- ❌ `{Lang}/sauv/` (sauvegardes)

---

### ✅ ÉTAPE 10 : VÉRIFICATIONS POST-UPLOAD

#### 10.1 Tests sur le Serveur
- [ ] `https://www.senseofthailand.com/{lang}/` s'affiche correctement
- [ ] Les images se chargent
- [ ] Les liens fonctionnent
- [ ] Les pages catégories sont accessibles
- [ ] Les pages produits sont accessibles

#### 10.2 Vérifications SEO avec des Outils
- [ ] **Google Search Console** : Soumettre le sitemap `/{lang}/sitemap.xml`
- [ ] **Vérifier les hreflang** : Utiliser un outil comme [hreflang Tags Testing Tool](https://technicalseo.com/tools/hreflang/)
- [ ] **Vérifier les meta tags** : Utiliser [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) ou [Twitter Card Validator](https://cards-dev.twitter.com/validator)

#### 10.3 Vérifications Finales
- [ ] **Toutes les pages** ont `lang="{lang}"` correct
- [ ] **Toutes les pages** ont des balises hreflang complètes
- [ ] **Toutes les pages** ont des canonical URLs correctes
- [ ] **Toutes les pages** ont des meta Open Graph en langue cible
- [ ] **Le sitemap.xml** est accessible et valide

---

## 🔧 PROBLÈMES COURANTS ET SOLUTIONS

### ❌ Problème : Les balises hreflang sont incorrectes
**Solution :** Vérifier que les scripts de génération incluent bien la génération des hreflang pour toutes les langues.

### ❌ Problème : Les meta Open Graph sont en français
**Solution :** Vérifier que les scripts lisent bien les colonnes `{lang}_auto` pour les meta tags.

### ❌ Problème : Les canonical URLs pointent vers `/` au lieu de `/{lang}/`
**Solution :** Vérifier que les scripts génèrent les canonical avec le bon préfixe de langue.

### ❌ Problème : Le sitemap.xml ne contient pas les URLs `/{lang}/`
**Solution :** Régénérer le sitemap ou le créer manuellement avec toutes les URLs.

### ❌ Problème : Les images ne se chargent pas
**Solution :** Vérifier les chemins relatifs selon la profondeur de la page :
- `index.html` → `../images/`
- `page_html/categories/` → `../../../images/`
- `page_html/products/` → `../../../images/`

---

## 📝 RÉSUMÉ : PROCESSUS COMPLET

1. ✅ **Préparer** : Vérifier que `Fr/` est fonctionnel
2. ✅ **Créer** : Exécuter `create_language_site.py`
3. ✅ **Traduire** : Charger les CSV dans Google Sheets, télécharger les traductions
4. ✅ **Générer** : Exécuter `generate_all_{lang}.py`
5. ✅ **Vérifier SEO** : Contrôler toutes les balises (hreflang, og:, canonical, lang)
6. ✅ **Tester local** : Vérifier que tout fonctionne
7. ✅ **Uploader** : Transférer uniquement les fichiers HTML, robots.txt, sitemap.xml
8. ✅ **Valider** : Tester sur le serveur et avec les outils SEO

---

## 🎯 POINTS CRITIQUES POUR LE RÉFÉRENCEMENT

1. **Balises hreflang** : Obligatoires pour Google (multilingue)
2. **Canonical URLs** : Évite le contenu dupliqué
3. **Meta Open Graph** : Améliore le partage sur réseaux sociaux
4. **Sitemap.xml** : Aide Google à indexer toutes les pages
5. **Langue HTML** : `lang="{lang}"` pour l'accessibilité et le SEO
6. **URLs absolues** : Utiliser `https://www.senseofthailand.com/{lang}/` dans les balises SEO

---

**✅ Une fois toutes ces étapes complétées, votre site est prêt pour l'upload et le référencement !**

