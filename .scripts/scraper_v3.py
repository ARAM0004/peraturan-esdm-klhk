#!/usr/bin/env python3
"""
Scraper V3 - ESDM & KLHK dengan support untuk command line arguments
File: .scripts/scraper_v3.py
"""

import argparse
import json
import os
from pathlib import Path

def load_config_file():
    """Load config from config.json if exists"""
    config_path = Path('config.json')
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Scraper V3 - ESDM & KLHK')
    
    # Load default from config.json if exists
    config = load_config_file()
    
    default_esdm = 'ESDM,energi,mineral,batubara,migas'
    default_klhk = 'KLHK,lingkungan,kehutanan,konservasi'
    default_perda = 'Perda,peraturan daerah'
    default_limit = 50
    
    if config:
        default_esdm = ','.join(config.get('keywords', {}).get('esdm', default_esdm.split(',')))
        default_klhk = ','.join(config.get('keywords', {}).get('klhk', default_klhk.split(',')))
        default_perda = ','.join(config.get('keywords', {}).get('perda', default_perda.split(',')))
        default_limit = config.get('limitPerRun', default_limit)
    
    parser.add_argument(
        '--keywords-esdm',
        type=str,
        default=default_esdm,
        help='Comma-separated ESDM keywords'
    )
    
    parser.add_argument(
        '--keywords-klhk',
        type=str,
        default=default_klhk,
        help='Comma-separated KLHK keywords'
    )
    
    parser.add_argument(
        '--keywords-perda',
        type=str,
        default=default_perda,
        help='Comma-separated Perda keywords'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=default_limit,
        help='Maximum items to scrape per run'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='regulations.json',
        help='Output file path'
    )
    
    return parser.parse_args()

def main():
    """Main scraper function"""
    args = parse_arguments()
    
    # Parse keywords
    keywords_esdm = [k.strip() for k in args.keywords_esdm.split(',')]
    keywords_klhk = [k.strip() for k in args.keywords_klhk.split(',')]
    keywords_perda = [k.strip() for k in args.keywords_perda.split(',')]
    
    print("="*50)
    print("🚀 Starting Scraper V3 - ESDM & KLHK")
    print("="*50)
    print(f"📊 Configuration:")
    print(f"   • ESDM Keywords: {keywords_esdm}")
    print(f"   • KLHK Keywords: {keywords_klhk}")
    print(f"   • Perda Keywords: {keywords_perda}")
    print(f"   • Limit: {args.limit}")
    print(f"   • Output: {args.output}")
    print("="*50)
    
    # Load existing data
    regulations_data = {
        'published': [],
        'pending': [],
        'lastUpdated': None
    }
    
    if os.path.exists(args.output):
        with open(args.output, 'r', encoding='utf-8') as f:
            regulations_data = json.load(f)
        print(f"✅ Loaded existing data: {len(regulations_data.get('published', []))} published, {len(regulations_data.get('pending', []))} pending")
    
    # TODO: Your actual scraping logic here
    # Example:
    scraped_count = 0
    
    # Scrape ESDM
    print(f"\n📡 Scraping ESDM with keywords: {keywords_esdm}")
    # esdm_results = scrape_esdm_site(keywords_esdm, args.limit)
    # regulations_data['pending'].extend(esdm_results)
    # scraped_count += len(esdm_results)
    
    # Scrape KLHK
    print(f"\n🌳 Scraping KLHK with keywords: {keywords_klhk}")
    # klhk_results = scrape_klhk_site(keywords_klhk, args.limit - scraped_count)
    # regulations_data['pending'].extend(klhk_results)
    # scraped_count += len(klhk_results)
    
    # Scrape Perda
    print(f"\n📜 Scraping Perda with keywords: {keywords_perda}")
    # perda_results = scrape_perda_site(keywords_perda, args.limit - scraped_count)
    # regulations_data['pending'].extend(perda_results)
    # scraped_count += len(perda_results)
    
    # Update timestamp
    from datetime import datetime
    regulations_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(regulations_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print(f"✅ Scraping complete!")
    print(f"   • Total scraped: {scraped_count}")
    print(f"   • Total pending: {len(regulations_data.get('pending', []))}")
    print(f"   • Total published: {len(regulations_data.get('published', []))}")
    print(f"   • Saved to: {args.output}")
    print("="*50)

if __name__ == '__main__':
    main()
