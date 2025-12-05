#!/usr/bin/env python3
"""
Script pour diagnostiquer pourquoi Google ne peut pas vérifier le sitemap
Usage: python3 diagnose_google_error.py [domaine]
"""

import sys
import requests
import xml.etree.ElementTree as ET
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

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else "makita-6kq.pages.dev"
    domain = domain.rstrip('/').replace('https://', '').replace('http://', '')
    sitemap_url = f"https://{domain}/sitemap-all.xml"
    
    print("=" * 70)
    print_header("🔍 DIAGNOSTIC : Pourquoi Google ne peut pas vérifier le sitemap")
    print("=" * 70)
    print()
    
    # Test 1: Accessibilité
    print_header("📋 TEST 1: Accessibilité du sitemap")
    print("-" * 70)
    
    try:
        response = requests.get(sitemap_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        })
        
        if response.status_code == 200:
            print_success(f"Accessible (HTTP {response.status_code})")
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            print_info("💡 Google ne peut pas accéder au sitemap si le code HTTP n'est pas 200")
            return
        
        # Test 2: Content-Type
        print()
        print_header("📋 TEST 2: Content-Type")
        print("-" * 70)
        
        content_type = response.headers.get('Content-Type', '')
        if 'xml' in content_type.lower():
            print_success(f"Content-Type correct: {content_type}")
        else:
            print_error(f"Content-Type incorrect: {content_type}")
            print_info("💡 Le Content-Type doit contenir 'xml' pour que Google le reconnaisse")
        
        # Test 3: Validité XML
        print()
        print_header("📋 TEST 3: Validité XML")
        print("-" * 70)
        
        try:
            root = ET.fromstring(response.content)
            if root.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset':
                print_success("Format XML valide")
                urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
                print_info(f"Nombre d'URLs: {len(urls)}")
                
                if len(urls) == 0:
                    print_error("Le sitemap est vide !")
                    print_info("💡 C'est probablement pour ça que Google dit 'impossible de vérifier'")
                    return
                
                # Vérifier quelques URLs
                print()
                print_info("Vérification de quelques URLs...")
                issues = []
                for i, url_elem in enumerate(urls[:10]):
                    loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        url = loc.text
                        # Tester l'accessibilité
                        try:
                            page_response = requests.head(url, timeout=5, allow_redirects=True)
                            if page_response.status_code != 200:
                                issues.append(f"{url} → HTTP {page_response.status_code}")
                        except:
                            issues.append(f"{url} → Inaccessible")
                
                if issues:
                    print_warning(f"{len(issues)} problème(s) détecté(s) sur les URLs testées")
                    for issue in issues[:5]:
                        print(f"  - {issue}")
                else:
                    print_success("Les URLs testées sont accessibles")
            else:
                print_error(f"Format XML invalide - Namespace incorrect: {root.tag}")
        except ET.ParseError as e:
            print_error(f"Erreur de parsing XML: {e}")
            print_info("💡 Le XML est malformé, Google ne peut pas le lire")
            return
        
        # Test 4: Taille du fichier
        print()
        print_header("📋 TEST 4: Taille du fichier")
        print("-" * 70)
        
        size_mb = len(response.content) / (1024 * 1024)
        if size_mb > 50:
            print_error(f"Fichier trop volumineux: {size_mb:.2f} MB (limite: 50 MB)")
            print_info("💡 Google ne peut pas lire les sitemaps de plus de 50 MB")
        else:
            print_success(f"Taille OK: {size_mb:.2f} MB")
        
        # Test 5: Nombre d'URLs
        print()
        print_header("📋 TEST 5: Nombre d'URLs")
        print("-" * 70)
        
        if len(urls) > 50000:
            print_error(f"Trop d'URLs: {len(urls)} (limite: 50,000)")
            print_info("💡 Divisez le sitemap en plusieurs fichiers")
        else:
            print_success(f"Nombre d'URLs OK: {len(urls)}")
        
        # Résumé
        print()
        print("=" * 70)
        print_header("📊 RÉSUMÉ")
        print("=" * 70)
        print()
        print_info("Si tous les tests sont OK mais Google dit toujours 'impossible de vérifier':")
        print("  1. Vérifiez dans Google Search Console les détails de l'erreur")
        print("  2. Attendez 1-2h (parfois Google met du temps à re-vérifier)")
        print("  3. Essayez de soumettre sitemap.xml (index) au lieu de sitemap-all.xml")
        print("  4. Vérifiez que robots.txt n'interdit pas l'accès")
        print()
        
    except requests.exceptions.RequestException as e:
        print_error(f"Erreur de connexion: {e}")
        print_info("💡 Vérifiez votre connexion internet et que le site est accessible")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic annulé")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

