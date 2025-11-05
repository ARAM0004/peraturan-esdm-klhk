#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper v3 - Full Config-Aware
Membaca keywords dan limit dari config.json
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re
import time
from pathlib import Path

class ConfigAwareScraperV3:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.results = []
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from config.json"""
        config_path = Path("config.json")
        
        if not config_path.exists():
            print("⚠️  config.json not found, using defaults")
            return self.get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Config loaded")
                return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration"""
        return {
            "scraper": {
                "esdm": {
                    "enabled": True,
                    "keywords": ["pertambangan", "mineral", "batubara"],
                    "types": ["Peraturan Menteri", "Keputusan Menteri"],
                    "limit": 10
                },
                "klhk": {
                    "enabled": True,
                    "keywords": ["pertambangan", "lingkungan", "kehutanan"],
                    "types": ["Peraturan Menteri", "Keputusan Menteri"],
                    "limit": 10
                }
            },
            "general": {
                "auto_publish_days": 7
            }
        }
    
    def matches_keywords(self, text, keywords):
        """Check if text contains any keywords"""
        if not keywords:
            return True
        
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    
    def scrape_esdm(self):
        """Scrape ESDM with config filters"""
        config = self.config['scraper'].get('esdm', {})
        
        if not config.get('enabled', True):
            print("⏸️  ESDM scraper disabled")
            return
        
        keywords = config.get('keywords', [])
        limit = config.get('limit', 10)
        
        print(f"\n🔍 Scraping ESDM...")
        print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
        print(f"   Limit: {limit}")
        
        try:
            url = "https://jdih.esdm.go.id/dokumen/peraturan"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', class_='item')
            
            print(f"   Found {len(items)} items")
            
            count = 0
            for item in items:
                if count >= limit:
                    break
                
                try:
                    title_elem = item.find('a', class_='text-primary')
                    if not title_elem:
                        continue
                    
                    full_title = title_elem.text.strip()
                    
                    # Filter by keywords
                    if not self.matches_keywords(full_title, keywords):
                        continue
                    
                    # Extract info
                    jenis_elem = item.find('a', class_='text-extra-dark-gray')
                    jenis = jenis_elem.text.strip() if jenis_elem else "Peraturan"
                    
                    year_elem = item.find('ul').find('li') if item.find('ul') else None
                    year = year_elem.text.strip() if year_elem else str(datetime.now().year)
                    
                    number_match = re.search(r'Nomor\s+(\S+\s+Tahun\s+\d{4})', full_title, re.IGNORECASE)
                    number = number_match.group(1) if number_match else f"{jenis} {year}"
                    
                    doc_link_elem = item.find('a', class_='text-theme-color')
                    if doc_link_elem and 'href' in doc_link_elem.attrs:
                        doc_path = doc_link_elem['href']
                        doc_link = f"https://jdih.esdm.go.id{doc_path}" if doc_path.startswith('/') else doc_path
                    else:
                        doc_link = url
                    
                    regulation = {
                        'id': f'esdm-{int(time.time() * 1000)}',
                        'title': full_title,
                        'number': number,
                        'ministry': 'ESDM',
                        'type': jenis,
                        'category': self.categorize(full_title),
                        'date': f'{year}-01-01',
                        'summary': self.generate_summary(full_title),
                        'link': doc_link,
                        'status': 'Aktif',
                        'scrapedDate': datetime.now().isoformat(),
                        'autoPublishDate': self.get_auto_publish_date(),
                        'verified': False,
                        'keywords_matched': [kw for kw in keywords if kw.lower() in full_title.lower()]
                    }
                    
                    self.results.append(regulation)
                    count += 1
                    print(f"   ✓ [{count}/{limit}] {number}")
                    time.sleep(0.5)
                    
                except Exception as e:
                    continue
            
            print(f"   Total scraped: {count}")
                    
        except Exception as e:
            print(f"❌ Error scraping ESDM: {e}")
    
    def scrape_klhk(self):
        """Scrape KLHK with config filters"""
        config = self.config['scraper'].get('klhk', {})
        
        if not config.get('enabled', True):
            print("⏸️  KLHK scraper disabled")
            return
        
        keywords = config.get('keywords', [])
        limit = config.get('limit', 10)
        
        print(f"\n🔍 Scraping KLHK...")
        print(f"   Keywords: {', '.join(keywords) if keywords else 'ALL'}")
        print(f"   Limit: {limit}")
        
        try:
            url = "https://jdih.kehutanan.go.id/new2/index.php/permenlhk"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', id='tablePeraturan')
            
            if not table:
                print("❌ Table not found")
                return
            
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
            print(f"   Found {len(rows)} rows")
            
            count = 0
            for row in rows:
                if count >= limit:
                    break
                
                try:
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                    
                    number_elem = cells[0].find('a', class_='no_peraturan')
                    if not number_elem:
                        continue
                    number = number_elem.text.strip()
                    
                    title = cells[2].text.strip()
                    
                    # Filter by keywords
                    if not self.matches_keywords(title, keywords):
                        continue
                    
                    # Extract type
                    reg_type = "Peraturan Menteri"
                    if 'SK MENHUT' in number.upper():
                        reg_type = "Keputusan Menteri"
                    
                    date_str = cells[1].text.strip()
                    try:
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                        date = date_obj.strftime('%Y-%m-%d')
                    except:
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    status_text = cells[3].text.strip()
                    status = 'Aktif' if 'berlaku' in status_text.lower() else 'Dicabut'
                    
                    download_btn = cells[4].find('a', class_='cta-btn2')
                    if download_btn and 'onclick' in download_btn.attrs:
                        onclick = download_btn['onclick']
                        link_match = re.search(r"window\.open\('([^']+)'", onclick)
                        doc_link = link_match.group(1) if link_match else url
                    else:
                        doc_link = url
                    
                    regulation = {
                        'id': f'klhk-{int(time.time() * 1000)}',
                        'title': title,
                        'number': number,
                        'ministry': 'KLHK',
                        'type': reg_type,
                        'category': self.categorize(title),
                        'date': date,
                        'summary': self.generate_summary(title),
                        'link': doc_link,
                        'status': status,
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
            
            print(f"   Total scraped: {count}")
                    
        except Exception as e:
            print(f"❌ Error scraping KLHK: {e}")
    
    def categorize(self, title):
        """Auto-categorize"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ['izin', 'perizinan']):
            return 'Perizinan'
        elif any(w in title_lower for w in ['lingkungan', 'amdal', 'limbah', 'kehutanan']):
            return 'Lingkungan'
        elif any(w in title_lower for w in ['k3', 'keselamatan']):
            return 'Keselamatan Kerja'
        elif any(w in title_lower for w in ['tambang', 'pertambangan', 'mineral', 'batubara']):
            return 'Teknis Pertambangan'
        elif any(w in title_lower for w in ['reklamasi', 'pascatambang']):
            return 'Reklamasi'
        elif any(w in title_lower for w in ['pajak', 'royalti', 'pnbp']):
            return 'Pajak & Royalti'
        else:
            return 'Lainnya'
    
    def generate_summary(self, title):
        """Generate summary"""
        title_clean = re.sub(r'Peraturan\s+Menteri.*?Nomor\s+\S+\s+Tahun\s+\d{4}\s+tentang\s+', '', title, flags=re.IGNORECASE)
        title_clean = re.sub(r'Keputusan\s+Menteri.*?Nomor\s+\S+\s+Tahun\s+\d{4}\s+tentang\s+', '', title_clean, flags=re.IGNORECASE)
        return f"Peraturan ini mengatur tentang {title_clean.lower()}"
    
    def get_auto_publish_date(self):
        """Get auto-publish date"""
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
        """Save results"""
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
            print(f"📊 Total new regulations: {len(new_regulations)}")
            print(f"💾 Saved to: {filename}")
            print("="*60)
            
            return len(new_regulations)
            
        except Exception as e:
            print(f"❌ Error saving: {e}")
            return 0

def main():
    print("="*60)
    print("🤖 CONFIG-AWARE SCRAPER v3.0")
    print("   JDIH ESDM & KLHK - Full Keyword Control")
    print("="*60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    scraper = ConfigAwareScraperV3()
    
    scraper.scrape_esdm()
    scraper.scrape_klhk()
    
    new_count = scraper.save_results('regulations.json')
    
    print()
    print(f"🎉 Done! Found {new_count} new regulations")

if __name__ == "__main__":
    main()
