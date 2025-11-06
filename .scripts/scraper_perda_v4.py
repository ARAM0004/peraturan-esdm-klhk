# ==========================================
# Scraper Perda V4
# File: .scripts/scraper_perda_v4.py
# ==========================================

"""
Scraper Perda V4 dengan support untuk command line arguments
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
    parser = argparse.ArgumentParser(description='Scraper Perda V4')
    
    # Load default from config.json if exists
    config = load_config_file()
    
    default_keywords = 'Perda,peraturan daerah,peraturan bupati,peraturan walikota'
    default_limit = 50
    
    if config:
        default_keywords = ','.join(config.get('keywords', {}).get('perda', default_keywords.split(',')))
        default_limit = config.get('limitPerRun', default_limit)
    
    parser.add_argument(
        '--keywords',
        type=str,
        default=default_keywords,
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
    keywords = [k.strip() for k in args.keywords.split(',')]
    
    print("="*50)
    print("🚀 Starting Scraper Perda V4")
    print("="*50)
    print(f"📊 Configuration:")
    print(f"   • Keywords: {keywords}")
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
    print(f"\n📡 Scraping Perda with keywords: {keywords}")
    # perda_results = scrape_perda_jdih(keywords, args.limit)
    # regulations_data['pending'].extend(perda_results)
    
    # Update timestamp
    from datetime import datetime
    regulations_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(regulations_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print(f"✅ Scraping complete!")
    print(f"   • Saved to: {args.output}")
    print("="*50)

if __name__ == '__main__':
    main()
