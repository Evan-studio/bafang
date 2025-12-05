# 🔧 Fix : Format du fichier _headers pour Cloudflare Pages

## ⚠️ Problème identifié

Le fichier `_headers` doit respecter un format spécifique pour Cloudflare Pages :
- **Indentation de 2 espaces** (pas de tabulations)
- **Format simple** : `Content-Type: application/xml` (sans charset pour les XML)
- **Emplacement** : À la racine du Build output

## ✅ Format correct pour Cloudflare Pages

```bash
# Pattern de chemin
/path
  Header-Name: value
```

**Important :** 2 espaces d'indentation (pas de tabulations)

## 📝 Fichier _headers corrigé

Le fichier a été simplifié selon les recommandations Cloudflare Pages :

```
/*.xml
  Content-Type: application/xml

/sitemap.xml
  Content-Type: application/xml

/sitemap-*.xml
  Content-Type: application/xml

/sitemap-all.xml
  Content-Type: application/xml
```

## 🔍 Vérifications

### 1. Emplacement du fichier

Le fichier `_headers` doit être à la **racine du Build output**.

Pour Cloudflare Pages :
- Si Build output = racine du projet → `_headers` à la racine ✅
- Si Build output = `dist` → `_headers` dans `dist/`
- Si Build output = `public` → `_headers` dans `public/`

### 2. Format du fichier

Vérifiez que :
- ✅ Indentation de 2 espaces (pas de tabs)
- ✅ Pas de caractères spéciaux
- ✅ Format : `path` puis ligne suivante avec 2 espaces + header

### 3. Test après déploiement

```bash
curl -I https://makita-6kq.pages.dev/sitemap-all.xml | grep -i content-type
```

Doit retourner : `content-type: application/xml`

## 🚀 Actions à faire

1. ✅ Fichier `_headers` corrigé (format simplifié)
2. ⏳ Déployer sur GitHub
3. ⏳ Attendre le déploiement Cloudflare (5-10 min)
4. ⏳ Vérifier les headers après déploiement

## 📊 Configuration Cloudflare Pages

Si vous avez accès aux paramètres de Build :

1. Allez sur https://dash.cloudflare.com
2. Pages → Votre projet → Settings
3. Vérifiez **Build configuration** :
   - **Build command** : (probablement vide pour site statique)
   - **Build output directory** : (probablement `/` ou vide)

Si Build output = `/` ou vide, le fichier `_headers` doit être à la racine ✅

## 💡 Note importante

Cloudflare Pages applique automatiquement `charset=utf-8` pour les fichiers XML, donc on peut simplifier le header à juste `Content-Type: application/xml`.

