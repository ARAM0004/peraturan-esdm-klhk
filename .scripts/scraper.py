#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re

class JDIHScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.results = []
        
    def scrape_esdm(self):
        """Scrape peraturan terbaru dari JDIH ESDM"""
        print("Scraping JDIH ESDM...")
        
        try:
            url = "https://jdih.esdm.go.id/peraturan/list"
            response = requests.get(url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Cari peraturan terbaru
            regulations = soup.find_all('div', class_='regulation-item', limit=10)
            
            for reg in regulations:
                try:
                    title_elem = reg.find('h3') or reg.find('a', class_='title')
                    number_elem = reg.find('span', class_='number')
                    date_elem = reg.find('span', class_='date')
                    link_elem = reg.find('a', href=True)
                    
                    if title_elem and number_elem:
                        regulation = {
                            'id': 'esdm-{}'.format(int(datetime.now().timestamp())),
                            'title': title_elem.text.strip(),
                            'number': number_elem.text.strip(),
                            'ministry': 'ESDM',
                            'category': self.categorize_regulation(title_elem.text),
                            'date': self.parse_date(date_elem.text if date_elem else ''),
                            'summary': self.generate_summary(title_elem.text),
                            'link': link_elem['href'] if link_elem else url,
                            'status': 'Aktif',
                            'scrapedDate': datetime.now().isoformat(),
                            'autoPublishDate': self.get_auto_publish_date(),
                            'verified': False
                        }
                        
                        self.results.append(regulation)
                        print("Found: {}".format(regulation['number']))
                        
                except Exception as e:
                    print("Error parsing regulation: {}".format(e))
                    continue
                    
        except Exception as e:
            print("Error scraping ESDM: {}".format(e))
            
    def scrape_klhk(self):
        """Scrape peraturan terbaru dari JDIH KLHK"""
        print("Scraping JDIH KLHK...")
        
        try:
            url = "https://jdih.menlhk.go.id/index.php/produk"
            response = requests.get(url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Cari peraturan terbaru
            regulations = soup.find_all('div', class_='product-item', limit=10)
            
            for reg in regulations:
                try:
                    title_elem = reg.find('h4') or reg.find('a')
                    number_elem = reg.find('span', class_='nomor')
                    date_elem = reg.find('span', class_='tanggal')
                    link_elem = reg.find('a', href=True)
                    
                    if title_elem and number_elem:
                        regulation = {
                            'id': 'klhk-{}'.format(int(datetime.now().timestamp())),
                            'title': title_elem.text.strip(),
                            'number': number_elem.text.strip(),
                            'ministry': 'KLHK',
                            'category': self.categorize_regulation(title_elem.text),
                            'date': self.parse_date(date_elem.text if date_elem else ''),
                            'summary': self.generate_summary(title_elem.text),
                            'link': link_elem['href'] if link_elem else url,
                            'status': 'Aktif',
                            'scrapedDate': datetime.now().isoformat(),
                            'autoPublishDate': self.get_auto_publish_date(),
                            'verified': False
                        }
                        
                        self.results.append(regulation)
                        print("Found: {}".format(regulation['number']))
                        
                except Exception as e:
                    print("Error parsing regulation: {}".format(e))
                    continue
                    
        except Exception as e:
            print("Error scraping KLHK: {}".format(e))
    
    def categorize_regulation(self, title):
        """Auto-categorize berdasarkan keywords dalam judul"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['izin', 'perizinan', 'persetujuan']):
            return 'Perizinan'
        elif any(word in title_lower for word in ['lingkungan', 'amdal', 'limbah', 'emisi']):
            return 'Lingkungan'
        elif any(word in title_lower for word in ['k3', 'keselamatan', 'kesehatan']):
            return 'Keselamatan Kerja'
        elif any(word in title_lower for word in ['tambang', 'eksplorasi', 'eksploitasi', 'mineral']):
            return 'Teknis Pertambangan'
        elif any(word in title_lower for word in ['reklamasi', 'pascatambang']):
            return 'Reklamasi'
        elif any(word in title_lower for word in ['pajak', 'royalti', 'pungutan']):
            return 'Pajak & Royalti'
        else:
            return 'Lainnya'
    
    def parse_date(self, date_str):
        """Parse tanggal dari berbagai format"""
        try:
            for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d %B %Y']:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
            
            return datetime.now().strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def generate_summary(self, title):
        """Generate ringkasan otomatis dari judul"""
        return "Peraturan ini mengatur tentang {}".format(title.lower())
    
    def get_auto_publish_date(self):
        """Get auto-publish date (7 hari dari sekarang)"""
        auto_date = datetime.now() + timedelta(days=7)
        return auto_date.isoformat()
    
    def remove_duplicates(self, existing_data):
        """Remove duplicates berdasarkan nomor peraturan"""
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
        """Save hasil scraping ke JSON file"""
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
            
            print("\nScraping complete!")
            print("Total new regulations found: {}".format(len(new_regulations)))
            print("Saved to: {}".format(filename))
            
            return len(new_regulations)
            
        except Exception as e:
            print("Error saving results: {}".format(e))
            return 0

def main():
    print("=" * 60)
    print("JDIH Auto-Scraper - ESDM & KLHK")
    print("=" * 60)
    print("Started at: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()
    
    scraper = JDIHScraper()
    
    scraper.scrape_esdm()
    print()
    scraper.scrape_klhk()
    print()
    
    new_count = scraper.save_results('regulations.json')
    
    print()
    print("=" * 60)
    print("Done! Found {} new regulations".format(new_count))
    print("=" * 60)

if __name__ == "__main__":
    main()
