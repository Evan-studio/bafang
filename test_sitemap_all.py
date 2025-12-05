#!/usr/bin/env python3
"""
Script pour tester spécifiquement sitemap-all.xml
Usage: python3 test_sitemap_all.py [domaine]
"""

import sys
import requests
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import urlparse

# Couleurs
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_info(msg): print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")
def print_success(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")
def print_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.NC}")
def print_header(msg): print(f"{Colors.CYAN}{msg}{Colors.NC}")

def test_local_sitemap(file_path):
    """Teste le sitemap local."""
    print_header("📁 TEST LOCAL DU SITEMAP")
    print("-" * 70)
    
    if not file_path.exists():
        print_error(f"Fichier non trouvé: {file_path}")
        return False
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Vérifier le namespace
        if root.tag != '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset':
            print_error("Format XML invalide - namespace incorrect")
            return False
        
        # Compter les URLs
        urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        url_count = len(urls)
        
        print_success(f"Fichier trouvé: {file_path.name}")
        print_info(f"Taille: {file_path.stat().st_size / 1024:.1f} KB")
        print_success(f"Nombre d'URLs: {url_count}")
        
        # Vérifier quelques URLs
        print()
        print_info("Exemples d'URLs (5 premières):")
        for i, url_elem in enumerate(urls[:5]):
            loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is not None:
                print(f"  {i+1}. {loc.text}")
        
        # Vérifier la structure
        print()
        print_info("Vérification de la structure...")
        issues = []
        
        for url_elem in urls:
            loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is None or not loc.text:
                issues.append("URL sans <loc>")
                continue
            
            # Vérifier que l'URL est valide
            try:
                parsed = urlparse(loc.text)
                if not parsed.scheme or not parsed.netloc:
                    issues.append(f"URL invalide: {loc.text}")
            except:
                issues.append(f"URL malformée: {loc.text}")
        
        if issues:
            print_warning(f"{len(issues)} problème(s) détecté(s)")
            for issue in issues[:5]:  # Afficher max 5 problèmes
                print(f"  - {issue}")
            if len(issues) > 5:
                print(f"  ... et {len(issues) - 5} autre(s) problème(s)")
        else:
            print_success("Structure XML valide")
        
        return True, url_count
        
    except ET.ParseError as e:
        print_error(f"Erreur de parsing XML: {e}")
        return False, 0
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False, 0

def test_remote_sitemap(url):
    """Teste le sitemap en ligne."""
    print()
    print_header("🌐 TEST EN LIGNE DU SITEMAP")
    print("-" * 70)
    
    try:
        print_info(f"Test de: {url}")
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SitemapTester/1.0)'
        })
        
        if response.status_code != 200:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
        
        print_success(f"Accessible (HTTP {response.status_code})")
        
        # Vérifier le Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'xml' in content_type.lower():
            print_success(f"Content-Type correct: {content_type}")
        else:
            print_warning(f"Content-Type: {content_type} (devrait contenir 'xml')")
        
        # Parser le XML
        try:
            root = ET.fromstring(response.content)
            urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            url_count = len(urls)
            
            print_success(f"Nombre d'URLs: {url_count}")
            print_info(f"Taille: {len(response.content) / 1024:.1f} KB")
            
            # Vérifier quelques URLs
            print()
            print_info("Exemples d'URLs (3 premières):")
            for i, url_elem in enumerate(urls[:3]):
                loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    print(f"  {i+1}. {loc.text}")
            
            return True, url_count
            
        except ET.ParseError as e:
            print_error(f"Erreur de parsing XML: {e}")
            return False, 0
            
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur de connexion: {e}")
        return False, 0

def test_sample_urls(sitemap_path, domain, sample_size=5):
    """Teste quelques URLs du sitemap pour vérifier qu'elles sont accessibles."""
    print()
    print_header("🔗 TEST D'ACCESSIBILITÉ DES URLs")
    print("-" * 70)
    
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        
        # Prendre un échantillon d'URLs
        import random
        sample = random.sample(urls, min(sample_size, len(urls)))
        
        accessible = 0
        for url_elem in sample:
            loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is None:
                continue
            
            url = loc.text
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    print_success(f"{url} → OK")
                    accessible += 1
                else:
                    print_warning(f"{url} → HTTP {response.status_code}")
            except:
                print_error(f"{url} → Inaccessible")
        
        print()
        print_info(f"Résultat: {accessible}/{len(sample)} URLs accessibles")
        
    except Exception as e:
        print_error(f"Erreur lors du test: {e}")

def main():
    """Fonction principale."""
    print("=" * 70)
    print_header("🧪 TEST DE SITEMAP-ALL.XML")
    print("=" * 70)
    print()
    
    # Déterminer le domaine
    if len(sys.argv) > 1:
        domain = sys.argv[1].rstrip('/').replace('https://', '').replace('http://', '')
    else:
        domain = "makita-6kq.pages.dev"
    
    base_dir = Path(__file__).parent
    sitemap_file = base_dir / 'sitemap-all.xml'
    sitemap_url = f"https://{domain}/sitemap-all.xml"
    
    # Test local
    success_local, local_count = test_local_sitemap(sitemap_file)
    
    if not success_local:
        print_error("Le test local a échoué. Corrigez le fichier avant de continuer.")
        sys.exit(1)
    
    # Test en ligne
    success_remote, remote_count = test_remote_sitemap(sitemap_url)
    
    # Comparer les comptes
    print()
    print_header("📊 COMPARAISON")
    print("-" * 70)
    print_info(f"URLs locales: {local_count}")
    if success_remote:
        print_info(f"URLs en ligne: {remote_count}")
        if local_count == remote_count:
            print_success("✅ Les deux versions correspondent")
        else:
            print_warning(f"⚠️  Différence détectée ({abs(local_count - remote_count)} URLs)")
            print_info("💡 Vous devrez peut-être redéployer le site")
    
    # Test d'accessibilité de quelques URLs
    if success_local:
        test_sample_urls(sitemap_file, domain, sample_size=5)
    
    # Résumé final
    print()
    print("=" * 70)
    if success_local and success_remote and local_count > 0:
        print_success("✅ SITEMAP-ALL.XML EST VALIDE ET PRÊT POUR GOOGLE")
        print()
        print_info("📤 Prochaines étapes:")
        print("   1. Déployez le site sur Cloudflare si ce n'est pas déjà fait")
        print(f"   2. Soumettez dans Google Search Console: {sitemap_url}")
        print("   3. Attendez 24-48h pour voir les résultats")
    else:
        print_warning("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print_info("💡 Vérifiez les erreurs ci-dessus et corrigez-les")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test annulé")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

