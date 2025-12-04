# Scripts de Génération Automatique

## 📋 Vue d'ensemble

Ces scripts permettent de générer automatiquement les pages HTML et de mettre à jour le site à partir de `config/categories.json`.

## 🎯 Scripts Disponibles

### 1. `generate_category_pages.py`
Génère les pages HTML pour chaque catégorie définie dans `config/categories.json`.

**Usage** :
```bash
python3 scripts/generate/generate_category_pages.py
```

**Ce qu'il fait** :
- Lit `config/categories.json`
- Utilise `couchage.html` comme template
- Génère une page HTML pour chaque catégorie
- Remplit automatiquement les meta tags, titres, etc.

### 2. `generate_menu.py`
Met à jour le menu dans `index.html` à partir des catégories.

**Usage** :
```bash
python3 scripts/generate/generate_menu.py
```

**Ce qu'il fait** :
- Met à jour le menu de navigation
- Met à jour la section catégories sur la page d'accueil

### 3. `generate_all.py` ⭐ (Recommandé)
Script principal qui exécute tout en une fois.

**Usage** :
```bash
python3 scripts/generate/generate_all.py
```

**Ce qu'il fait** :
1. Génère toutes les pages de catégories
2. Met à jour le menu
3. Met à jour la section catégories

## 🔄 Workflow pour un Nouveau Site

### Étape 1 : Configurer les catégories
Modifiez `config/categories.json` avec vos catégories :

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
        "title": "Tentes - Mon Site",
        "description": "..."
      }
    }
  ]
}
```

### Étape 2 : Ajouter les images
Placez les images dans `images/categories/` :
- `tentes.webp`
- `mobilier.webp`
- etc.

### Étape 3 : Générer les pages
```bash
python3 scripts/generate/generate_all.py
```

### Étape 4 : Générer les fichiers JSON produits
Utilisez vos scripts existants pour créer `products-{slug}.json` pour chaque catégorie.

## ✅ Avantages

- ✅ **Automatique** : Plus besoin de créer manuellement chaque page
- ✅ **Cohérent** : Toutes les pages suivent le même template
- ✅ **Maintenable** : Un seul fichier (`categories.json`) à modifier
- ✅ **Rapide** : Génération en quelques secondes

## 📝 Notes

- Le template de base est `couchage.html`
- Les pages générées remplacent les existantes
- Le menu est mis à jour automatiquement
- Les meta tags sont remplis depuis `categories.json`

## 🔧 Personnalisation

Pour modifier le template :
1. Modifiez `couchage.html` comme vous le souhaitez
2. Relancez `generate_all.py`
3. Toutes les pages seront régénérées avec le nouveau template



