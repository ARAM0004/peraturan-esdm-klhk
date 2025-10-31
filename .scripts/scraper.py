#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re
import time

class JDIHScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.results = []
        
    def scrape_esdm(self):
        """Scrape peraturan terbaru dari JDIH ESDM"""
        print("Scraping JDIH ESDM...")
        
        try:
            url = "https://jdih.esdm.go.id/dokumen/peraturan"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all regulation items
            items = soup.find_all('div', class_='item')
            print("Found {} items from ESDM".format(len(items)))
            
            for item in items[:10]:  # Limit to 10 latest
                try:
                    # Extract jenis peraturan (Keputusan Menteri, Peraturan Menteri, etc)
                    jenis_elem = item.find('a', class_='text-extra-dark-gray')
                    jenis = jenis_elem.text.strip() if jenis_elem else "Peraturan"
                    
                    # Extract year
                    year_elem = item.find('ul').find('li') if item.find('ul') else None
                    year = year_elem.text.strip() if year_elem else str(datetime.now().year)
                    
                    # Extract title and number (combined)
                    title_elem = item.find('a', class_='text-primary')
                    if not title_elem:
                        continue
                        
                    full_title = title_elem.text.strip()
                    
                    # Extract regulation number from title
                    number_match = re.search(r'Nomor\s+(\S+\s+Tahun\s+\d{4})', full_title, re.IGNORECASE)
                    if number_match:
                        number = number_match.group(1)
                    else:
                        number = "{} {}".format(jenis, year)
                    
                    # Extract document link
                    doc_link_elem = item.find('a', class_='text-theme-color')
                    if doc_link_elem and 'href' in doc_link_elem.attrs:
                        doc_path = doc_link_elem['href']
                        if doc_path.startswith('/'):
                            doc_link = "https://jdih.esdm.go.id{}".format(doc_path)
                        else:
                            doc_link = doc_path
                    else:
                        doc_link = url
                    
                    # Build regulation object
                    regulation = {
                        'id': 'esdm-{}'.format(int(time.time() * 1000)),
                        'title': full_title,
                        'number': number,
                        'ministry': 'ESDM',
                        'category': self.categorize_regulation(full_title),
                        'date': '{}-01-01'.format(year),  # Default to January 1st if no specific date
                        'summary': self.generate_summary(full_title),
                        'link': doc_link,
                        'status': 'Aktif',
                        'scrapedDate': datetime.now().isoformat(),
                        'autoPublishDate': self.get_auto_publish_date(),
                        'verified': False
                    }
                    
                    self.results.append(regulation)
                    print("  ✓ {}".format(number))
                    time.sleep(0.5)  # Be polite
                        
                except Exception as e:
                    print("  ⚠ Error parsing item: {}".format(e))
                    continue
                    
        except Exception as e:
            print("❌ Error scraping ESDM: {}".format(e))
            
    def scrape_klhk(self):
        """Scrape peraturan terbaru dari JDIH KLHK"""
        print("\nScraping JDIH KLHK...")
        
        try:
            url = "https://jdih.kehutanan.go.id/new2/index.php/permenlhk"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find table rows
            table = soup.find('table', id='tablePeraturan')
            if not table:
                print("❌ Table not found")
                return
                
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
            print("Found {} rows from KLHK".format(len(rows)))
            
            for row in rows[:10]:  # Limit to 10 latest
                try:
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                    
                    # Extract number
                    number_elem = cells[0].find('a', class_='no_peraturan')
                    if not number_elem:
                        continue
                    number = number_elem.text.strip()
                    
                    # Extract date
                    date_str = cells[1].text.strip()
                    try:
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                        date = date_obj.strftime('%Y-%m-%d')
                    except:
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Extract title
                    title = cells[2].text.strip()
                    
                    # Extract status
                    status_text = cells[3].text.strip()
                    status = 'Aktif' if 'berlaku' in status_text.lower() else 'Dicabut'
                    
                    # Extract document link
                    download_btn = cells[4].find('a', class_='cta-btn2')
                    if download_btn and 'onclick' in download_btn.attrs:
                        onclick = download_btn['onclick']
                        # Extract URL from window.open()
                        link_match = re.search(r"window\.open\('([^']+)'", onclick)
                        if link_match:
                            doc_link = link_match.group(1)
                        else:
                            doc_link = url
                    else:
                        doc_link = url
                    
                    # Build regulation object
                    regulation = {
                        'id': 'klhk-{}'.format(int(time.time() * 1000)),
                        'title': title,
                        'number': number,
                        'ministry': 'KLHK',
                        'category': self.categorize_regulation(title),
                        'date': date,
                        'summary': self.generate_summary(title),
                        'link': doc_link,
                        'status': status,
                        'scrapedDate': datetime.now().isoformat(),
                        'autoPublishDate': self.get_auto_publish_date(),
                        'verified': False
                    }
                    
                    self.results.append(regulation)
                    print("  ✓ {}".format(number))
                    time.sleep(0.5)  # Be polite
                        
                except Exception as e:
                    print("  ⚠ Error parsing row: {}".format(e))
                    continue
                    
        except Exception as e:
            print("❌ Error scraping KLHK: {}".format(e))
    
    def categorize_regulation(self, title):
        """Auto-categorize berdasarkan keywords dalam judul"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['izin', 'perizinan', 'persetujuan', 'tata cara']):
            return 'Perizinan'
        elif any(word in title_lower for word in ['lingkungan', 'amdal', 'limbah', 'emisi', 'konservasi', 'kehutanan', 'mangrove']):
            return 'Lingkungan'
        elif any(word in title_lower for word in ['k3', 'keselamatan', 'kesehatan', 'pelindungan']):
            return 'Keselamatan Kerja'
        elif any(word in title_lower for word in ['tambang', 'eksplorasi', 'eksploitasi', 'mineral', 'batubara', 'pertambangan']):
            return 'Teknis Pertambangan'
        elif any(word in title_lower for word in ['reklamasi', 'pascatambang', 'rehabilitasi']):
            return 'Reklamasi'
        elif any(word in title_lower for word in ['pajak', 'royalti', 'pungutan', 'pnbp', 'biaya']):
            return 'Pajak & Royalti'
        else:
            return 'Lainnya'
    
    def generate_summary(self, title):
        """Generate ringkasan otomatis dari judul"""
        # Clean title
        title_clean = re.sub(r'Peraturan\s+Menteri.*?Nomor\s+\S+\s+Tahun\s+\d{4}\s+tentang\s+', '', title, flags=re.IGNORECASE)
        title_clean = re.sub(r'Keputusan\s+Menteri.*?Nomor\s+\S+\s+Tahun\s+\d{4}\s+tentang\s+', '', title_clean, flags=re.IGNORECASE)
        
        return "Peraturan ini mengatur tentang {}".format(title_clean.lower())
    
    def get_auto_publish_date(self):
        """Get auto-publish date (7 hari dari sekarang)"""
        auto_date = datetime.now() + timedelta(days=7)
        return auto_date.isoformat()
    
    def remove_duplicates(self, existing_data):
        """Remove duplicates berdasarkan nomor peraturan"""
        existing_numbers = set()
        
        # Get existing regulation numbers
        for reg in existing_data.get('published', []):
            existing_numbers.add(reg.get('number', ''))
        
        for reg in existing_data.get('pending', []):
            existing_numbers.add(reg.get('number', ''))
        
        # Filter out duplicates
        unique_results = []
        for reg in self.results:
            if reg['number'] not in existing_numbers:
                unique_results.append(reg)
                existing_numbers.add(reg['number'])
        
        return unique_results
    
    def save_results(self, filename='regulations.json'):
        """Save hasil scraping ke JSON file"""
        try:
            # Load existing data
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = {'published': [], 'pending': [], 'lastUpdated': ''}
            
            # Remove duplicates
            new_regulations = self.remove_duplicates(existing_data)
            
            # Add new regulations to pending
            existing_data['pending'].extend(new_regulations)
            existing_data['lastUpdated'] = datetime.now().isoformat()
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*60)
            print("✅ Scraping complete!")
            print("📊 Total new regulations found: {}".format(len(new_regulations)))
            print("💾 Saved to: {}".format(filename))
            print("="*60)
            
            return len(new_regulations)
            
        except Exception as e:
            print("❌ Error saving results: {}".format(e))
            return 0

def main():
    print("="*60)
    print("🤖 JDIH Auto-Scraper - ESDM & KLHK")
    print("="*60)
    print("⏰ Started at: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print()
    
    scraper = JDIHScraper()
    
    # Scrape both sources
    scraper.scrape_esdm()
    scraper.scrape_klhk()
    
    # Save results
    new_count = scraper.save_results('regulations.json')
    
    print()
    print("🎉 Done! Found {} new regulations".format(new_count))

if __name__ == "__main__":
    main()
