# Architecture Template - Site d'Affiliation

## 🎯 Objectif
Ce site est un **template réutilisable** pour créer rapidement d'autres sites avec :
- Différentes marques
- Différents produits
- Différents domaines
- Même structure HTML/CSS

## 📊 Analyse de la Structure Actuelle

### ✅ Points Positifs
1. **config.json** existe déjà pour logo, hero, meta
2. **Structure HTML modulaire** avec sections réutilisables
3. **Chargement dynamique** via JavaScript

### ⚠️ Points à Améliorer

#### 1. URLs Hardcodées
- `https://votresite.com` présent dans tous les fichiers HTML (hreflang)
- Liens relatifs OK, mais domaines absolus à configurer

#### 2. Contenus Hardcodés
- Textes dans le HTML (FAQ, témoignages, stats, présentation marque)
- Noms de catégories dans le menu
- Textes du footer
- Descriptions de sections

#### 3. Structure de Données
- `products-*.json` séparés par catégorie
- Pas de centralisation des métadonnées produits
- Chemins d'images en dur dans le JSON

## 🏗️ Architecture Proposée

### Structure Recommandée

```
site-template/
├── templates/              # Templates HTML (NE JAMAIS MODIFIER)
│   ├── index.html
│   ├── category.html
│   ├── product.html
│   └── ...
├── config/
│   ├── site.json          # Configuration générale
│   ├── content.json       # Tous les textes
│   ├── categories.json    # Configuration catégories
│   └── domain.json        # URLs et domaines
├── data/
│   └── products/          # Données produits par catégorie
│       ├── tentes.json
│       ├── couchage.json
│       └── ...
├── assets/
│   ├── images/
│   │   ├── logo.webp
│   │   ├── hero.webp
│   │   └── products/
│   └── ...
└── README.md
```

### Fichiers de Configuration

#### 1. `config/site.json`
```json
{
  "brand": {
    "name": "Naturehike",
    "description": "Description de la marque"
  },
  "logo": {
    "type": "image",
    "image": "assets/images/logo.webp"
  },
  "colors": {
    "primary": "#e60012",
    "secondary": "#ff4757"
  }
}
```

#### 2. `config/content.json`
```json
{
  "menu": {
    "home": "Accueil",
    "categories": ["Tentes", "Mobilier", "Couchage", "Cuisine", "Vêtement"]
  },
  "hero": {
    "title": "...",
    "subtitle": "...",
    "button": "..."
  },
  "sections": {
    "presentation": {
      "title": "...",
      "content": "..."
    },
    "faq": [
      {"question": "...", "answer": "..."}
    ],
    "testimonials": [...],
    "stats": [...]
  },
  "footer": {
    "contact": "contact@naturehike-shop.com",
    "links": [...]
  }
}
```

#### 3. `config/domain.json`
```json
{
  "base_url": "https://naturehike-shop.com",
  "default_lang": "fr",
  "languages": {
    "fr": "https://naturehike-shop.com/fr/",
    "en": "https://naturehike-shop.com/en/"
  }
}
```

#### 4. `config/categories.json`
```json
{
  "categories": [
    {
      "id": "tentes",
      "name": "Tentes",
      "slug": "tentes",
      "image": "assets/images/categories/tentes.webp",
      "meta": {
        "title": "...",
        "description": "..."
      }
    }
  ]
}
```

## 🔧 Modifications Nécessaires

### 1. Centraliser les URLs
- Créer `config/domain.json` avec base_url
- Remplacer tous les `https://votresite.com` par une variable JS
- Générer les hreflang dynamiquement

### 2. Externaliser les Contenus
- Déplacer tous les textes dans `config/content.json`
- Charger via JavaScript au lieu de hardcoder
- Permettre remplacement rapide

### 3. Standardiser les Produits
- Format JSON uniforme
- Chemins d'images relatifs depuis `assets/`
- Métadonnées complètes dans chaque produit

### 4. Script de Génération
- Script pour créer un nouveau site à partir du template
- Copie des templates
- Initialisation des configs avec nouvelles valeurs

## 📝 Plan d'Action

1. **Phase 1 : Analyse** ✅ (en cours)
2. **Phase 2 : Restructuration**
   - Créer structure de dossiers
   - Séparer templates et configs
3. **Phase 3 : Migration**
   - Déplacer contenus vers JSON
   - Remplacer hardcoding par chargement dynamique
4. **Phase 4 : Documentation**
   - Guide de création d'un nouveau site
   - Template de configs

## ❓ Questions à Valider

1. Voulez-vous garder la structure actuelle ou tout restructurer ?
2. Préférez-vous un seul `config.json` ou plusieurs fichiers ?
3. Faut-il un script d'initialisation pour créer un nouveau site ?
4. Comment gérez-vous les images ? (dossier unique ou par marque ?)



