#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perda Scraper v4 - Config-Aware
Membaca keywords dan limit dari config.json
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import re
from pathlib import Path

class PerdaScraperV4:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.results = []
        self.config = self.load_config()
        
    def load_config(self):
        """Load config"""
        config_path = Path("config.json")
        
        if not config_path.exists():
            return self.get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self.get_default_config()
    
    def get_default_config(self):
        return {
            "scraper": {
                "perda": {
                    "enabled": True,
                    "keywords": ["pertambangan", "tambang", "mineral"],
                    "limit": 20
                }
            },
            "general": {
                "auto_publish_days": 7
            }
        }
    
    def matches_keywords(self, text, keywords):
        if not keywords:
            return True
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    
    def scrape_province(self, url, name, code, keywords, limit):
        """Scrape single province"""
        print(f"\n🔍 Scraping {name}...")
        print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
        print(f"   Limit: {limit}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            selectors = [
                'div[class*="card"]',
                'div[class*="item"]',
                'article',
                '.artikel_wrap'
            ]
            
            items = []
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    items = found
                    break
            
            count = 0
            for item in items[:limit]:
                try:
                    text = item.get_text(strip=True)
                    if not text or len(text) < 20:
                        continue
                    
                    if not self.matches_keywords(text, keywords):
                        continue
                    
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    title = title_elem.get_text(strip=True) if title_elem else text[:200]
                    
                    link_elem = item.find('a')
                    if link_elem and link_elem.get('href'):
                        href = link_elem['href']
                        if not href.startswith('http'):
                            href = url.rstrip('/') + '/' + href.lstrip('/')
                    else:
                        href = url
                    
                    number_match = re.search(r'(Perda|Peraturan Daerah).*?No\.?\s*(\d+.*?Tahun\s+\d{4})', title, re.IGNORECASE)
                    number = number_match.group(0) if number_match else f"Perda {name} {count + 1}"
                    
                    year_match = re.search(r'Tahun\s+(\d{4})', title)
                    year = year_match.group(1) if year_match else str(datetime.now().year)
                    
                    regulation = {
                        'id': f'perda-{code.lower()}-{int(time.time() * 1000)}-{count}',
                        'title': title[:300],
                        'number': number,
                        'ministry': 'Perda',
                        'category': self.categorize(title),
                        'date': f'{year}-01-01',
                        'summary': f'Peraturan Daerah {name} tentang {title[:100]}',
                        'link': href,
                        'status': 'Aktif',
                        'provinsi': name,
                        'provinsi_code': code,
                        'scrapedDate': datetime.now().isoformat(),
                        'autoPublishDate': self.get_auto_publish_date(),
                        'verified': False,
                        'keywords_matched': [kw for kw in keywords if kw.lower() in title.lower()]
                    }
                    
                    self.results.append(regulation)
                    count += 1
                    print(f"   ✓ [{count}/{limit}] {number}")
                    time.sleep(0.5)
                    
                except:
                    continue
            
            print(f"   Total: {count}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def categorize(self, title):
        title_lower = title.lower()
        if any(w in title_lower for w in ['tambang', 'pertambangan', 'mineral']):
            return 'Teknis Pertambangan'
        elif any(w in title_lower for w in ['lingkungan', 'kehutanan']):
            return 'Lingkungan'
        elif any(w in title_lower for w in ['izin', 'perizinan']):
            return 'Perizinan'
        else:
            return 'Perda'
    
    def get_auto_publish_date(self):
        days = self.config.get('general', {}).get('auto_publish_days', 7)
        return (datetime.now() + timedelta(days=days)).isoformat()
    
    def remove_duplicates(self, existing_data):
        existing_numbers = set()
        for reg in existing_data.get('published', []):
            existing_numbers.add(reg.get('number', ''))
        for reg in existing_data.get('pending', []):
            existing_numbers.add(reg.get('number', ''))
        
        unique = []
        for reg in self.results:
            if reg['number'] not in existing_numbers:
                unique.append(reg)
                existing_numbers.add(reg['number'])
        return unique
    
    def save_results(self, filename='regulations.json'):
        try:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = {'published': [], 'pending': [], 'lastUpdated': ''}
            
            new_regs = self.remove_duplicates(existing_data)
            existing_data['pending'].extend(new_regs)
            existing_data['lastUpdated'] = datetime.now().isoformat()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*60)
            print(f"✅ Complete! New Perda: {len(new_regs)}")
            print("="*60)
            return len(new_regs)
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0

def main():
    print("="*60)
    print("🏛️  PERDA SCRAPER v4.0 - Config-Aware")
    print("="*60)
    
    scraper = PerdaScraperV4()
    perda_config = scraper.config['scraper'].get('perda', {})
    
    if not perda_config.get('enabled', True):
        print("⏸️  Perda scraper disabled")
        return
    
    keywords = perda_config.get('keywords', [])
    limit = perda_config.get('limit', 20)
    
    # Scrape Sulut
    scraper.scrape_province(
        "https://jdih.sulutprov.go.id/",
        "Sulawesi Utara",
        "SULUT",
        keywords,
        limit
    )
    time.sleep(2)
    
    # Scrape Kaltara
    scraper.scrape_province(
        "https://jdih.kaltaraprov.go.id/",
        "Kalimantan Utara",
        "KALTARA",
        keywords,
        limit
    )
    
    scraper.save_results()

if __name__ == "__main__":
    main()
