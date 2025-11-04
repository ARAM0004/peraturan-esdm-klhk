#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perda Scraper v3 - Improved dengan Web Analysis
FIXED untuk Sulawesi Utara (Next.js) dan Kalimantan Utara (Yii)
Berdasarkan analisis struktur HTML sebenarnya
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import re
from pathlib import Path

class PerdaScraperV3:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.results = []
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration dari config.json"""
        config_path = Path("config.json")
        
        if not config_path.exists():
            print("⚠️  config.json tidak ditemukan, menggunakan default")
            return self.get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Config loaded successfully")
                return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration"""
        return {
            "scraper": {
                "perda": {
                    "enabled": True,
                    "keywords": ["pertambangan", "tambang", "mineral", "galian"],
                    "provinces": [
                        {
                            "name": "Sulawesi Utara",
                            "code": "SULUT",
                            "url": "https://jdih.sulutprov.go.id/",
                            "enabled": True,
                            "type": "nextjs"
                        },
                        {
                            "name": "Kalimantan Utara",
                            "code": "KALTARA",
                            "url": "https://jdih.kaltaraprov.go.id/",
                            "enabled": True,
                            "type": "yii"
                        }
                    ],
                    "limit": 20
                }
            },
            "general": {
                "auto_publish_days": 7
            }
        }
    
    def matches_keywords(self, text, keywords):
        """Check if text contains any of the keywords"""
        if not keywords:  # Jika keywords kosong, ambil semua
            return True
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def scrape_sulut(self, base_url, keywords, limit):
        """
        Scrape JDIH Sulawesi Utara (Next.js/React based)
        Struktur: Modern JS framework dengan API endpoints
        """
        print(f"\n🔍 Scraping Sulawesi Utara (Next.js)...")
        print(f"   Base URL: {base_url}")
        print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
        
        try:
            # Coba akses halaman produk hukum/peraturan daerah
            search_urls = [
                f"{base_url}dokumen/group/peraturan-daerah",
                f"{base_url}produk-hukum",
                base_url
            ]
            
            count = 0
            for url in search_urls:
                if count >= limit:
                    break
                    
                try:
                    print(f"   Trying URL: {url}")
                    response = requests.get(url, headers=self.headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Cari berbagai kemungkinan selector untuk card/item peraturan
                    selectors = [
                        'div[class*="card"]',
                        'div[class*="regulation"]',
                        'div[class*="item"]',
                        'article',
                        'div[class*="peraturan"]',
                        'div[class*="dokumen"]'
                    ]
                    
                    items = []
                    for selector in selectors:
                        found = soup.select(selector)
                        if found:
                            items = found
                            print(f"   Found {len(found)} items with selector: {selector}")
                            break
                    
                    if not items:
                        continue
                    
                    for item in items[:limit - count]:
                        try:
                            # Extract text content
                            text = item.get_text(strip=True)
                            if not text or len(text) < 20:
                                continue
                            
                            # Filter by keywords
                            if not self.matches_keywords(text, keywords):
                                continue
                            
                            # Extract title
                            title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                            title = title_elem.get_text(strip=True) if title_elem else text[:200]
                            
                            # Extract link
                            link_elem = item.find('a')
                            if link_elem and link_elem.get('href'):
                                href = link_elem['href']
                                if not href.startswith('http'):
                                    href = base_url.rstrip('/') + '/' + href.lstrip('/')
                            else:
                                href = url
                            
                            # Extract number/date
                            number_match = re.search(r'(Perda|Peraturan Daerah).*?No\.?\s*(\d+.*?Tahun\s+\d{4})', title, re.IGNORECASE)
                            if number_match:
                                number = number_match.group(0)
                            else:
                                number = f"Perda Sulut {count + 1}"
                            
                            year_match = re.search(r'Tahun\s+(\d{4})', title)
                            year = year_match.group(1) if year_match else str(datetime.now().year)
                            
                            regulation = {
                                'id': f'perda-sulut-{int(time.time() * 1000)}-{count}',
                                'title': title[:300],
                                'number': number,
                                'ministry': 'Perda',
                                'category': self.categorize(title),
                                'date': f'{year}-01-01',
                                'summary': f'Peraturan Daerah Sulawesi Utara tentang {title[:100]}',
                                'link': href,
                                'status': 'Aktif',
                                'provinsi': 'Sulawesi Utara',
                                'provinsi_code': 'SULUT',
                                'scrapedDate': datetime.now().isoformat(),
                                'autoPublishDate': self.get_auto_publish_date(),
                                'verified': False,
                                'keywords_matched': [kw for kw in keywords if kw.lower() in title.lower()]
                            }
                            
                            self.results.append(regulation)
                            count += 1
                            print(f"   ✓ [{count}/{limit}] {number}")
                            time.sleep(0.5)
                            
                        except Exception as e:
                            continue
                    
                    if count > 0:
                        break  # Success, exit loop
                        
                except Exception as e:
                    print(f"   ⚠️ Error with URL {url}: {e}")
                    continue
            
            print(f"   Total scraped: {count}")
                    
        except Exception as e:
            print(f"❌ Error scraping Sulut: {e}")
    
    def scrape_kaltara(self, base_url, keywords, limit):
        """
        Scrape JDIH Kalimantan Utara (Yii Framework)
        Struktur: Traditional PHP dengan class-based selectors
        """
        print(f"\n🔍 Scraping Kalimantan Utara (Yii Framework)...")
        print(f"   Base URL: {base_url}")
        print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
        
        try:
            # Coba beberapa URL endpoint
            search_urls = [
                base_url,
                f"{base_url}produk_hukum/clear/4-peraturan-daerah-perda",
                f"{base_url}search/filter"
            ]
            
            count = 0
            for url in search_urls:
                if count >= limit:
                    break
                    
                try:
                    print(f"   Trying URL: {url}")
                    response = requests.get(url, headers=self.headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Selector khusus untuk Kaltara (Yii structure)
                    selectors = [
                        '.artikel_wrap',  # Dari analisis HTML
                        '.card-body',
                        '.panel-body',
                        'div[class*="item"]',
                        'table tr',
                        '.list-group-item'
                    ]
                    
                    items = []
                    for selector in selectors:
                        found = soup.select(selector)
                        if found:
                            items = found
                            print(f"   Found {len(found)} items with selector: {selector}")
                            break
                    
                    if not items:
                        continue
                    
                    for item in items[:limit - count]:
                        try:
                            # Extract text
                            text = item.get_text(strip=True)
                            if not text or len(text) < 20:
                                continue
                            
                            # Filter by keywords
                            if not self.matches_keywords(text, keywords):
                                continue
                            
                            # Extract title - cari di berbagai elemen
                            title = None
                            for selector in ['a.artikel_title', '.artikel_title', 'h3', 'h4', 'a', 'strong']:
                                title_elem = item.select_one(selector)
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                                    if len(title) > 20:
                                        break
                            
                            if not title:
                                title = text[:200]
                            
                            # Extract link
                            link_elem = item.find('a')
                            if link_elem and link_elem.get('href'):
                                href = link_elem['href']
                                if not href.startswith('http'):
                                    href = base_url.rstrip('/') + '/' + href.lstrip('/')
                            else:
                                href = url
                            
                            # Extract number
                            number_match = re.search(r'(Perda|Peraturan Daerah).*?No\.?\s*(\d+.*?Tahun\s+\d{4})', title, re.IGNORECASE)
                            if number_match:
                                number = number_match.group(0)
                            else:
                                number = f"Perda Kaltara {count + 1}"
                            
                            year_match = re.search(r'Tahun\s+(\d{4})', title)
                            year = year_match.group(1) if year_match else str(datetime.now().year)
                            
                            regulation = {
                                'id': f'perda-kaltara-{int(time.time() * 1000)}-{count}',
                                'title': title[:300],
                                'number': number,
                                'ministry': 'Perda',
                                'category': self.categorize(title),
                                'date': f'{year}-01-01',
                                'summary': f'Peraturan Daerah Kalimantan Utara tentang {title[:100]}',
                                'link': href,
                                'status': 'Aktif',
                                'provinsi': 'Kalimantan Utara',
                                'provinsi_code': 'KALTARA',
                                'scrapedDate': datetime.now().isoformat(),
                                'autoPublishDate': self.get_auto_publish_date(),
                                'verified': False,
                                'keywords_matched': [kw for kw in keywords if kw.lower() in title.lower()]
                            }
                            
                            self.results.append(regulation)
                            count += 1
                            print(f"   ✓ [{count}/{limit}] {number}")
                            time.sleep(0.5)
                            
                        except Exception as e:
                            continue
                    
                    if count > 0:
                        break  # Success
                        
                except Exception as e:
                    print(f"   ⚠️ Error with URL {url}: {e}")
                    continue
            
            print(f"   Total scraped: {count}")
                    
        except Exception as e:
            print(f"❌ Error scraping Kaltara: {e}")
    
    def categorize(self, title):
        """Auto-categorize"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['tambang', 'pertambangan', 'mineral', 'galian']):
            return 'Teknis Pertambangan'
        elif any(word in title_lower for word in ['lingkungan', 'kehutanan', 'hutan']):
            return 'Lingkungan'
        elif any(word in title_lower for word in ['izin', 'perizinan']):
            return 'Perizinan'
        else:
            return 'Perda'
    
    def get_auto_publish_date(self):
        """Get auto-publish date dari config"""
        days = self.config.get('general', {}).get('auto_publish_days', 7)
        auto_date = datetime.now() + timedelta(days=days)
        return auto_date.isoformat()
    
    def remove_duplicates(self, existing_data):
        """Remove duplicates"""
        existing_numbers = set()
        
        for reg in existing_data.get('published', []):
            existing_numbers.add(reg.get('number', ''))
        
        for reg in existing_data.get('pending', []):
            existing_numbers.add(reg.get('number', ''))
        
        unique_results = []
        for reg in self.results:
            if reg['number'] not in existing_numbers:
                unique_results.append(reg)
                existing_numbers.add(reg['number'])
        
        return unique_results
    
    def save_results(self, filename='regulations.json'):
        """Save hasil scraping"""
        try:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = {'published': [], 'pending': [], 'lastUpdated': ''}
            
            new_regulations = self.remove_duplicates(existing_data)
            
            existing_data['pending'].extend(new_regulations)
            existing_data['lastUpdated'] = datetime.now().isoformat()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*60)
            print("✅ Scraping complete!")
            print(f"📊 Total new Perda: {len(new_regulations)}")
            print(f"💾 Saved to: {filename}")
            print("="*60)
            
            return len(new_regulations)
            
        except Exception as e:
            print(f"❌ Error saving: {e}")
            return 0

def main():
    print("="*60)
    print("🏛️  PERDA SCRAPER v3.0 - Web-Structure Aware")
    print("   FIXED: Sulawesi Utara (Next.js) & Kalimantan Utara (Yii)")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scraper = PerdaScraperV3()
    
    # Get config
    perda_config = scraper.config['scraper'].get('perda', {})
    
    if not perda_config.get('enabled', True):
        print("⏸️  Perda scraper disabled in config")
        return
    
    keywords = perda_config.get('keywords', [])
    limit = perda_config.get('limit', 20)
    
    print("📋 Configuration:")
    print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
    print(f"   Limit: {limit} per province")
    print()
    
    # Scrape Sulut (Next.js)
    scraper.scrape_sulut(
        "https://jdih.sulutprov.go.id/",
        keywords,
        limit
    )
    time.sleep(2)
    
    # Scrape Kaltara (Yii)
    scraper.scrape_kaltara(
        "https://jdih.kaltaraprov.go.id/",
        keywords,
        limit
    )
    
    # Save results
    new_count = scraper.save_results('regulations.json')
    
    print()
    print(f"🎉 Done! Found {new_count} new Perda regulations")
    print()
    print("💡 Tips:")
    print("   - Jika hasil kurang, coba kosongkan keywords untuk ambil semua")
    print("   - Tingkatkan limit untuk lebih banyak hasil")
    print("   - Check manual di website JDIH jika ada masalah")

if __name__ == "__main__":
    main()
