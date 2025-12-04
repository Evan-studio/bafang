# Système de Correspondance Catégories

## 🎯 Problème
- Le CSV contient `category_id` (numérique, ex: 3)
- Les menus ont des noms (ex: "Couchage", "Tentes")
- Les dossiers/images doivent correspondre
- Le nombre et noms de catégories peuvent varier selon le site

## ✅ Solution : Fichier de Mapping

### Structure : `config/categories.json`

```json
{
  "categories": [
    {
      "id": 1,
      "slug": "tentes",
      "name": "Tentes",
      "menu_order": 1,
      "image": "images/categories/tentes.webp",
      "page": "tentes.html",
      "meta": {
        "title": "Tentes - Affiliation AliExpress",
        "description": "Découvrez notre sélection de tentes..."
      }
    },
    {
      "id": 2,
      "slug": "mobilier",
      "name": "Mobilier",
      "menu_order": 2,
      "image": "images/categories/mobilier.webp",
      "page": "mobilier.html",
      "meta": {
        "title": "Mobilier - Affiliation AliExpress",
        "description": "Découvrez notre sélection de mobilier..."
      }
    },
    {
      "id": 3,
      "slug": "couchage",
      "name": "Couchage",
      "menu_order": 3,
      "image": "images/categories/couchage.webp",
      "page": "couchage.html",
      "meta": {
        "title": "Couchage - Affiliation AliExpress",
        "description": "Découvrez notre sélection de couchage..."
      }
    }
  ]
}
```

## 📊 Correspondance CSV → Catégories

### Dans le CSV : `category_id`
```csv
product_id,category_id,...
1005009443652299,3,...
```

### Mapping : `category_id: 3` → `slug: "couchage"` → `name: "Couchage"`

## 📁 Organisation des Images Produits

### Option 1 : Par category_id (Recommandé)
```
images/products/
├── category_1/          # Tentes
│   └── [product_id]/
├── category_2/          # Mobilier
│   └── [product_id]/
└── category_3/          # Couchage
    └── [product_id]/
```

**Avantage** : Stable même si le nom change

### Option 2 : Par slug
```
images/products/
├── tentes/
│   └── [product_id]/
├── mobilier/
│   └── [product_id]/
└── couchage/
    └── [product_id]/
```

**Avantage** : Plus lisible, mais change si le nom change

### Option 3 : Par product_id uniquement (Actuel)
```
images/products/
└── [product_id]/        # Pas de sous-dossier catégorie
    ├── image_1.jpg
    └── video.mp4
```

**Avantage** : Simple, mais pas de séparation par catégorie

## 🔄 Logique Recommandée

### 1. Fichier de mapping : `config/categories.json`
- Fait le lien entre `category_id` (CSV) et `slug`/`name` (site)
- Définit l'ordre du menu
- Contient les meta tags

### 2. Organisation images : Par `category_id` dans le nom du dossier
```
images/products/
└── [category_id]_[product_id]/
    ├── image_1.jpg
    └── video.mp4
```

**Exemple** : `3_1005009443652299/` = catégorie 3 (couchage), produit 1005009443652299

### 3. Alternative : Dossier par catégorie
```
images/products/
├── category_3/          # Dossier catégorie 3
│   └── 1005009443652299/
│       ├── image_1.jpg
│       └── video.mp4
```

## 💡 Recommandation Finale

**Structure hybride** :
- **Dossiers produits** : `images/products/[product_id]/` (simple, actuel)
- **Mapping** : `config/categories.json` fait le lien CSV → Site
- **Fichiers JSON produits** : Contiennent `category_id` du CSV
- **JavaScript** : Utilise le mapping pour afficher dans la bonne catégorie

**Avantages** :
- ✅ Pas besoin de réorganiser les dossiers existants
- ✅ Mapping flexible (change de nom = change juste le JSON)
- ✅ CSV reste simple avec category_id
- ✅ Facile à maintenir

## 📝 Exemple de Workflow

1. **CSV** : `category_id: 3`
2. **Mapping** : `config/categories.json` → `id: 3` = `slug: "couchage"`, `name: "Couchage"`
3. **Images** : `images/products/1005009443652299/` (product_id uniquement)
4. **Affichage** : JavaScript charge le mapping, filtre les produits par category_id, affiche dans la page "couchage.html"

## 🔧 Utilisation dans les Scripts

### Python
```python
from scripts.get_category_info import get_category_by_id

# Obtenir les infos d'une catégorie depuis le CSV
category_id = 3  # Depuis all_products.csv
cat_info = get_category_by_id(category_id)
# Retourne: {"id": 3, "slug": "couchage", "name": "Couchage", "page": "couchage.html", ...}
```

### JavaScript (dans les pages HTML)
```javascript
// Charger config/categories.json
fetch('config/categories.json')
  .then(r => r.json())
  .then(data => {
    const categories = data.categories;
    // Filtrer les produits par category_id
    const products = allProducts.filter(p => p.category_id === 3);
    // Afficher dans la bonne page
  });
```

## ✅ Solution Implémentée

1. **Fichier de mapping** : `config/categories.json` créé
2. **Script utilitaire** : `scripts/get_category_info.py` pour accéder au mapping
3. **Structure images** : `images/products/[product_id]/` (simple, stable)
4. **Correspondance** : CSV `category_id` → JSON mapping → Site `slug`/`name`

