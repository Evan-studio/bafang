# Guide : Mise à jour de index.html depuis translations.csv

## Vue d'ensemble

Le script `scripts/generate/update_index_from_csv.py` met à jour **uniquement** la page `index.html` avec les données du fichier `translations.csv`. Ce script ne modifie aucune autre page et n'utilise que les informations du CSV.

## Utilisation

```bash
python3 scripts/generate/update_index_from_csv.py
```

## Structure des données dans translations.csv

Le script lit uniquement la colonne `en` (anglais) du fichier CSV. Voici les clés utilisées :

### Menu et Catégories

- `home.en` : Texte pour le lien "Home" dans le menu
- `menu.{slug}` : Nom de la catégorie dans le menu
- `descripton.{slug}` : Description textuelle de la catégorie
- `meta.title.menu.{slug}` : Meta title pour la page catégorie
- `meta.des.menu.{slug}` : Meta description pour la page catégorie

**Exemple :**
```csv
key,en
menu.test1en,Test Category
descripton.test1en,This is a test category description
meta.title.menu.test1en,Test Category - AliExpress
meta.des.menu.test1en,Discover our test category products
```

### Page d'accueil (Homepage)

- `site.meta.title` : Titre SEO de la page
- `site.meta.description` : Description SEO
- `homepage.hero.title` : Titre principal (hero section)
- `homepage.hero.subtitle` : Sous-titre (hero section)
- `homepage.hero.button` : Texte du bouton hero
- `homepage.categories.title` : Titre de la section catégories
- `homepage.bestsellers.title` : Titre de la section best sellers
- `homepage.presentation.title` : Titre de la section présentation
- `homepage.presentation.content` : Contenu de la section présentation
- `homepage.advantages.title` : Titre de la section avantages
- `homepage.stats.title` : Titre de la section statistiques
- `homepage.faq.title` : Titre de la section FAQ
- `homepage.testimonials.title` : Titre de la section témoignages

### Footer

- `footer.link.home` : Texte du lien "Home"
- `footer.link.sitemap` : Texte du lien "Site map"
- `footer.link.conditions` : Texte du lien "Terms of Use"
- `footer.link.mentions` : Texte du lien "Legal notice"
- `footer.link.policy` : Texte du lien "Privacy Policy"
- `footer.copyright` : Texte du copyright

## Comment les slugs sont créés

Les **slugs** sont des versions simplifiées des noms de catégories utilisées dans les URLs. Ils sont créés automatiquement à partir du nom de la catégorie (colonne `menu.{slug}` du CSV) grâce à la fonction `slugify()`.

### Processus de création d'un slug

1. **Mise en minuscules**
   - "Test Category" → "test category"

2. **Suppression des caractères spéciaux**
   - Garde uniquement : lettres, chiffres, espaces, tirets
   - "Test Category!" → "Test Category"

3. **Remplacement des espaces multiples par des tirets simples**
   - "Test   Category" → "test-category"

4. **Suppression des accents (normalisation Unicode)**
   - Conversion en forme NFD (Normalization Form Decomposed)
   - Encodage ASCII pour supprimer les accents
   - "Découvrez" → "Decouvrez"

5. **Nettoyage des tirets en début/fin**
   - "-test-category-" → "test-category"

### Exemples de création de slugs

| Nom original | Slug généré |
|-------------|-------------|
| `Test Category` | `test-category` |
| `Découvrez nos Produits!` | `decouvrez-nos-produits` |
| `Catégorie 123` | `categorie-123` |
| `Test   Multiple   Spaces` | `test-multiple-spaces` |
| `Produit & Accessoires` | `produit-accessoires` |

### Utilisation des slugs

Les slugs sont utilisés pour :
- **Les URLs des pages catégories** : `page_html/categories/{slug}.html`
- **Les chemins des images** : `images/categories/{slug}.webp`
- **Les liens dans le menu** : `<a href="page_html/categories/{slug}.html">`

**Exemple :**
Si `menu.test1en` = "Test Category", alors :
- Slug généré : `test-category`
- URL de la page : `page_html/categories/test-category.html`
- Image de la catégorie : `images/categories/test-category.webp`

## Fonctionnalités du script

Le script met à jour automatiquement :

1. ✅ **Meta tags** (title, description)
2. ✅ **Menu de navigation** (avec les catégories du CSV)
3. ✅ **Section catégories** (cartes avec images)
4. ✅ **Section hero** (titre, sous-titre, bouton)
5. ✅ **Titres de sections** (catégories, best sellers, FAQ, etc.)
6. ✅ **Footer** (liens et copyright)

## Notes importantes

- ⚠️ Le script ne modifie **que** `index.html`, pas les autres pages
- ⚠️ Le script utilise **uniquement** les données du CSV (colonne `en`)
- ⚠️ Les catégories doivent avoir **toutes** les clés nécessaires :
  - `menu.{slug}`
  - `descripton.{slug}`
  - `meta.title.menu.{slug}`
  - `meta.des.menu.{slug}`
  
  Si une clé manque, la catégorie est ignorée.

- ⚠️ Le script **écrase** le contenu actuel de `index.html` avec les nouvelles données du CSV

## Structure des catégories dans le CSV

Pour qu'une catégorie soit prise en compte, elle doit avoir exactement ces 4 clés dans le CSV :

```csv
key,en
menu.test1en,Test Category
descripton.test1en,This is a test category description
meta.title.menu.test1en,Test Category - AliExpress Affiliate
meta.des.menu.test1en,Discover our test category products on AliExpress
```

**Ordre :** Les catégories sont triées alphabétiquement par slug dans le menu et la section catégories.

## Résolution de problèmes

### Le menu n'apparaît pas correctement

- Vérifiez que toutes les clés nécessaires sont présentes dans le CSV
- Vérifiez que la colonne `en` contient bien les valeurs
- Vérifiez qu'il n'y a pas d'erreurs dans le CSV

### Les slugs ne correspondent pas

- Les slugs sont générés automatiquement à partir du nom de la catégorie
- Si vous changez le nom, le slug change aussi
- Les anciens fichiers HTML peuvent rester (orphanés)

### Le script ne trouve pas le CSV

- Vérifiez que `translations.csv` est à la racine du projet
- Vérifiez les permissions de lecture du fichier


