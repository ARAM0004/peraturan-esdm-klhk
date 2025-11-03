#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perda Scraper v2 - Config-Aware
FIXED untuk Sulawesi Utara dan Kalimantan Utara
Membaca keywords dari config.json
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import re
from pathlib import Path

class PerdaScraperV2:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                    "keywords": ["pertambangan", "tambang", "mineral"],
                    "provinces": [
                        {
                            "name": "Sulawesi Utara",
                            "code": "SULUT",
                            "url": "https://jdih.sulutprov.go.id/",
                            "enabled": True
                        },
                        {
                            "name": "Kalimantan Utara",
                            "code": "KALTARA",
                            "url": "https://jdih.kaltaraprov.go.id/",
                            "enabled": True
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
    
    def scrape_provinsi(self, url, provinsi_name, provinsi_code):
        """Scrape perda dari JDIH provinsi dengan filter keywords"""
        config = self.config['scraper'].get('perda', {})
        keywords = config.get('keywords', [])
        limit = config.get('limit', 20)
        
        print(f"\n🔍 Scraping {provinsi_name} ({url})")
        print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
        print(f"   Limit: {limit}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try multiple selectors
            selectors = [
                '.card-body',
                '.panel-body',
                '.post',
                '.peraturan-item',
                '.regulation-item',
                '.item',
                'article',
                '.list-group-item'
            ]
            
            cards = []
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    cards = found
                    print(f"   Found {len(found)} items with selector: {selector}")
                    break
            
            if not cards:
                print("   ⚠️  No items found")
                return
            
            count = 0
            for card in cards:
                if count >= limit:
                    break
                
                try:
                    title = card.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # Filter by keywords
                    if not self.matches_keywords(title, keywords):
                        continue
                    
                    # Extract link
                    link = card.find('a')
                    href = link['href'] if link and link.get('href') else None
                    
                    if href and not href.startswith('http'):
                        base_url = url.rstrip('/')
                        href = base_url + '/' + href.lstrip('/')
                    
                    # Extract number
                    number_match = re.search(r'(Perda|Peraturan Daerah).*?No\.?\s*(\d+.*?Tahun\s+\d{4})', title, re.IGNORECASE)
                    if number_match:
                        number = number_match.group(0)
                    else:
                        number = f"Perda {provinsi_code} No. {count + 1}"
                    
                    # Extract year
                    year_match = re.search(r'Tahun\s+(\d{4})', title)
                    year = year_match.group(1) if year_match else str(datetime.now().year)
                    
                    regulation = {
                        'id': f'perda-{provinsi_code.lower()}-{int(time.time() * 1000)}',
                        'title': title[:300],  # Limit title length
                        'number': number,
                        'ministry': 'Perda',
                        'category': self.categorize(title),
                        'date': f'{year}-01-01',
                        'summary': f'Peraturan Daerah {provinsi_name} tentang {title[:100]}',
                        'link': href or url,
                        'status': 'Aktif',
                        'provinsi': provinsi_name,
                        'provinsi_code': provinsi_code,
                        'scrapedDate': datetime.now().isoformat(),
                        'autoPublishDate': self.get_auto_publish_date(),
                        'verified': False,
                        'keywords_matched': [kw for kw in keywords if kw.lower() in title.lower()]
                    }
                    
                    self.results.append(regulation)
                    count += 1
                    print(f"   ✓ [{count}/{limit}] {number}")
                    time.sleep(0.3)
                    
                except Exception as e:
                    continue
            
            print(f"   Total scraped: {count}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
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
    print("🏛️  PERDA SCRAPER v2.0 - Config-Aware")
    print("   FIXED: Sulawesi Utara & Kalimantan Utara")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scraper = PerdaScraperV2()
    
    # Get config
    perda_config = scraper.config['scraper'].get('perda', {})
    
    if not perda_config.get('enabled', True):
        print("⏸️  Perda scraper disabled in config")
        return
    
    # Display config
    print("📋 Configuration:")
    print(f"   Keywords: {', '.join(perda_config.get('keywords', []))}")
    print(f"   Limit: {perda_config.get('limit', 20)} per province")
    print()
    
    # FIXED: Always scrape SULUT and KALTARA
    provinces = [
        ("https://jdih.sulutprov.go.id/", "Sulawesi Utara", "SULUT"),
        ("https://jdih.kaltaraprov.go.id/", "Kalimantan Utara", "KALTARA")
    ]
    
    # Scrape each province
    for url, name, code in provinces:
        scraper.scrape_provinsi(url, name, code)
        time.sleep(1)  # Delay between provinces
    
    # Save results
    new_count = scraper.save_results('regulations.json')
    
    print()
    print(f"🎉 Done! Found {new_count} new Perda regulations")

if __name__ == "__main__":
    main()
