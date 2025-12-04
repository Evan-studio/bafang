# Structure des Images - Organisation par Thème

## 🎯 Objectif
Organiser les images par type pour faciliter le changement de site/thème.

## 📁 Structure Proposée

```
images/
├── logo/
│   └── logo.webp                    # Logo principal
├── hero/
│   └── hero.webp                    # Image hero page d'accueil
├── categories/
│   ├── tentes.webp
│   ├── mobilier.webp
│   ├── couchage.webp
│   ├── cuisine.webp
│   └── vetement.webp
├── testimonials/
│   ├── client1.webp                 # Photo témoignage 1
│   ├── client2.webp
│   ├── client3.webp
│   └── client4.webp
├── products/
│   └── [product_id]/
│       ├── image_1.webp
│       ├── image_2.webp
│       └── video.mp4
└── favicon/
    └── favicon.ico
```

## 🔄 Alternative : Structure par Thème/Site

Si vous voulez changer TOUT le site d'un coup :

```
images/
├── themes/
│   ├── naturehike/
│   │   ├── logo.webp
│   │   ├── hero.webp
│   │   ├── categories/
│   │   └── testimonials/
│   ├── decathlon/
│   │   ├── logo.webp
│   │   ├── hero.webp
│   │   └── ...
│   └── default/
│       └── ...
└── products/                        # Commun à tous les sites
    └── [product_id]/
```

## ✅ Solution Recommandée : Structure par Type

**Avantages :**
- ✅ Simple et claire
- ✅ Facile à remplacer (remplacer tout le dossier `logo/` par exemple)
- ✅ Pas besoin de modifier le code
- ✅ Compatible avec config.json

**Structure :**
```
images/
├── logo/
│   └── logo.webp
├── hero/
│   └── hero.webp
├── categories/
│   └── *.webp
├── testimonials/
│   └── *.webp
├── products/
│   └── [product_id]/
└── favicon/
    └── favicon.ico
```

## 📝 Configuration dans config.json

```json
{
  "site": {
    "logo": {
      "image": "images/logo/logo.webp"
    },
    "hero": {
      "image": "images/hero/hero.webp"
    }
  },
  "categories": {
    "tentes": "images/categories/tentes.webp",
    "mobilier": "images/categories/mobilier.webp"
  },
  "testimonials": {
    "images": [
      "images/testimonials/client1.webp",
      "images/testimonials/client2.webp"
    ]
  }
}
```

## 🔄 Processus de Changement de Site

### Option 1 : Remplacer les dossiers
1. Supprimer `images/logo/`
2. Copier le nouveau dossier `logo/` avec le nouveau logo
3. Répéter pour `hero/`, `categories/`, `testimonials/`
4. Mettre à jour `config.json` si nécessaire

### Option 2 : Script de changement
```bash
# change-theme.sh
./change-theme.sh naturehike
# Copie automatiquement tous les dossiers du thème
```

## 💡 Recommandation Finale

**Structure par type** (plus simple) :
- `images/logo/` → Un seul logo.webp
- `images/hero/` → Une seule hero.webp
- `images/categories/` → Toutes les images catégories
- `images/testimonials/` → Toutes les photos témoignages
- `images/products/` → Tous les produits (commun)

**Pour changer de site :**
1. Remplacer les fichiers dans chaque dossier
2. Garder la même structure
3. Pas besoin de modifier le code !



