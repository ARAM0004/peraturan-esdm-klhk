#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time

class PerdaScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.results = []
        
    def scrape_provinsi(self, url, provinsi, filter_keyword=None):
        """Scrape perda dari JDIH provinsi"""
        print("Scraping {} ({})...".format(provinsi, url))
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try multiple selectors (different JDIH sites use different structures)
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
                    print("  Found {} items with selector: {}".format(len(found), selector))
                    break
            
            if not cards:
                print("  No items found with any selector")
                return
            
            count = 0
            for card in cards[:20]:  # Limit 20 per province
                try:
                    title = card.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    
                    # Filter berdasarkan keyword
                    if filter_keyword:
                        keywords = filter_keyword.lower().split(',')
                        if not any(kw.strip() in title.lower() for kw in keywords):
                            continue
                    
                    # Extract link
                    link = card.find('a')
                    href = link['href'] if link and link.get('href') else None
                    
                    if href and not href.startswith('http'):
                        base_url = url.rstrip('/')
                        href = base_url + '/' + href.lstrip('/')
                    
                    # Extract number if possible
                    import re
                    number_match = re.search(r'(Perda|Peraturan Daerah).*?No\.?\s*(\d+)', title, re.IGNORECASE)
                    if number_match:
                        number = number_match.group(0)
                    else:
                        number = "{} No. {}".format(provinsi, count + 1)
                    
                    regulation = {
                        'id': 'perda-{}-{}'.format(provinsi.lower().replace(' ', '-'), int(time.time() * 1000)),
                        'title': title[:200],  # Limit title length
                        'number': number,
                        'ministry': 'Perda',
                        'category': self.categorize(title),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'summary': 'Peraturan Daerah {} tentang {}'.format(provinsi, title[:100]),
                        'link': href or url,
                        'status': 'Aktif',
                        'provinsi': provinsi,
                        'scrapedDate': datetime.now().isoformat(),
                        'autoPublishDate': self.get_auto_publish_date(),
                        'verified': False
                    }
                    
                    self.results.append(regulation)
                    count += 1
                    print("  + {}".format(number))
                    time.sleep(0.3)  # Be polite
                    
                except Exception as e:
                    continue
            
            print("  Total found: {}".format(count))
                    
        except Exception as e:
            print("  ERROR scraping {}: {}".format(provinsi, e))
    
    def categorize(self, title):
        """Auto-categorize berdasarkan keywords"""
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
        auto_date = datetime.now() + timedelta(days=7)
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
            print("Scraping complete!")
            print("Total new Perda found: {}".format(len(new_regulations)))
            print("Saved to: {}".format(filename))
            print("="*60)
            
            return len(new_regulations)
            
        except Exception as e:
            print("ERROR saving: {}".format(e))
            return 0

def main():
    print("="*60)
    print("SCRAPER PERDA - Peraturan Daerah")
    print("="*60)
    print("Started at: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()
    
    # Filter keyword (ubah sesuai kebutuhan)
    filter_keyword = "pertambangan,tambang,mineral"  # Multiple keywords dipisah koma
    # Set None untuk tanpa filter
    
    scraper = PerdaScraper()
    
    # Daftar JDIH Provinsi (tambahkan sesuai kebutuhan)
    provinces = [
        ("https://jdih.sulutprov.go.id/", "Sulawesi Utara"),
        ("https://jdih.kaltaraprov.go.id/", "Kalimantan Utara"),
        ("https://jdih.kaltimprov.go.id/", "Kalimantan Timur"),
        ("https://jdih.papua.go.id/", "Papua"),
        ("https://jdih.ntbprov.go.id/", "Nusa Tenggara Barat"),
    ]
    
    for url, provinsi in provinces:
        scraper.scrape_provinsi(url, provinsi, filter_keyword)
        print()
    
    new_count = scraper.save_results('regulations.json')
    
    print()
    print("Done! Found {} new Perda regulations".format(new_count))
    if filter_keyword:
        print("(filtered by: '{}')".format(filter_keyword))

if __name__ == "__main__":
    main()
