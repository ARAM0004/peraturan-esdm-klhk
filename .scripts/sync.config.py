#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk sinkronisasi config dari web interface ke GitHub Actions
Baca config.json yang di-generate dari web, lalu update workflow files
"""

import json
import yaml
import os
from pathlib import Path

def load_web_config():
    """Load config dari file yang di-export dari web"""
    config_path = Path("config/portal-config.json")
    
    if not config_path.exists():
        print("❌ File config/portal-config.json tidak ditemukan")
        print("💡 Export config dari web interface terlebih dahulu")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_scraper_workflow(config):
    """Update .github/workflows/scraper.yml dengan config baru"""
    workflow_path = Path(".github/workflows/scraper.yml")
    
    if not workflow_path.exists():
        print("❌ File scraper.yml tidak ditemukan")
        return False
    
    with open(workflow_path, 'r') as f:
        workflow = yaml.safe_load(f)
    
    # Update schedule
    schedule = config['scraper']['esdm_klhk']['schedule']
    workflow['on']['schedule'] = [{'cron': schedule}]
    
    print(f"✅ Updated ESDM/KLHK schedule to: {schedule}")
    
    with open(workflow_path, 'w') as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    return True

def update_perda_workflow(config):
    """Update .github/workflows/scraper_perda.yml dengan config baru"""
    workflow_path = Path(".github/workflows/scraper_perda.yml")
    
    if not workflow_path.exists():
        print("❌ File scraper_perda.yml tidak ditemukan")
        return False
    
    with open(workflow_path, 'r') as f:
        workflow = yaml.safe_load(f)
    
    # Update schedule
    schedule = config['scraper']['perda']['schedule']
    workflow['on']['schedule'] = [{'cron': schedule}]
    
    print(f"✅ Updated Perda schedule to: {schedule}")
    
    with open(workflow_path, 'w') as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    return True

def update_scraper_script(config):
    """Update .scripts/scraper.py dengan limit baru"""
    script_path = Path(".scripts/scraper.py")
    
    if not script_path.exists():
        print("❌ File scraper.py tidak ditemukan")
        return False
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update limit
    limit = config['scraper']['esdm_klhk']['limit']
    
    # Replace limit in both ESDM and KLHK functions
    content = content.replace(
        "for item in items[:10]:",
        f"for item in items[:{limit}]:"
    )
    content = content.replace(
        "for row in rows[:10]:",
        f"for row in rows[:{limit}]:"
    )
    
    # Update auto-publish days
    auto_days = config['scraper']['esdm_klhk']['auto_publish_days']
    content = content.replace(
        "auto_date = datetime.now() + timedelta(days=7)",
        f"auto_date = datetime.now() + timedelta(days={auto_days})"
    )
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated ESDM/KLHK limit to: {limit}")
    print(f"✅ Updated auto-publish days to: {auto_days}")
    
    return True

def update_perda_script(config):
    """Update .scripts/scraper_perda.py dengan config baru"""
    script_path = Path(".scripts/scraper_perda.py")
    
    if not script_path.exists():
        print("❌ File scraper_perda.py tidak ditemukan")
        return False
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update limit
    limit = config['scraper']['perda']['limit']
    content = content.replace(
        "for card in cards[:20]:",
        f"for card in cards[:{limit}]:"
    )
    
    # Update keywords
    keywords = config['scraper']['perda']['keywords']
    content = content.replace(
        'filter_keyword = "pertambangan,tambang,mineral"',
        f'filter_keyword = "{keywords}"'
    )
    
    # Update provinces list
    provinces = config['scraper']['perda']['provinces']
    enabled_provinces = [p for p in provinces if p['enabled']]
    
    provinces_code = "provinces = [\n"
    for prov in enabled_provinces:
        provinces_code += f'        ("{prov["url"]}", "{prov["name"]}"),\n'
    provinces_code += "    ]"
    
    # Find and replace provinces section
    import re
    pattern = r'provinces = \[(.*?)\]'
    content = re.sub(pattern, provinces_code, content, flags=re.DOTALL)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated Perda limit to: {limit}")
    print(f"✅ Updated keywords to: {keywords}")
    print(f"✅ Updated provinces: {len(enabled_provinces)} enabled")
    
    return True

def generate_config_summary(config):
    """Generate summary of config changes"""
    print("\n" + "="*60)
    print("📋 CONFIGURATION SUMMARY")
    print("="*60)
    
    print("\n🤖 ESDM & KLHK Scraper:")
    print(f"   Status: {'✅ Enabled' if config['scraper']['esdm_klhk']['enabled'] else '❌ Disabled'}")
    print(f"   Schedule: {config['scraper']['esdm_klhk']['schedule']}")
    print(f"   Limit: {config['scraper']['esdm_klhk']['limit']} items")
    print(f"   Auto-publish: {config['scraper']['esdm_klhk']['auto_publish_days']} days")
    
    print("\n🏛️  Perda Scraper:")
    print(f"   Status: {'✅ Enabled' if config['scraper']['perda']['enabled'] else '❌ Disabled'}")
    print(f"   Schedule: {config['scraper']['perda']['schedule']}")
    print(f"   Limit: {config['scraper']['perda']['limit']} items per province")
    print(f"   Keywords: {config['scraper']['perda']['keywords']}")
    
    enabled_provs = [p['name'] for p in config['scraper']['perda']['provinces'] if p['enabled']]
    print(f"   Provinces: {', '.join(enabled_provs)}")
    
    print("\n🎨 Display Settings:")
    print(f"   Items per page: {config['display']['itemsPerPage']}")
    print(f"   Show stats: {'✅ Yes' if config['display']['showStats'] else '❌ No'}")
    print(f"   Show last update: {'✅ Yes' if config['display']['showLastUpdate'] else '❌ No'}")
    
    print("\n" + "="*60)

def main():
    print("="*60)
    print("🔄 CONFIG SYNC TOOL")
    print("="*60)
    print()
    
    # Load config
    config = load_web_config()
    if not config:
        return
    
    print("✅ Config loaded successfully\n")
    
    # Update workflows
    print("📝 Updating workflow files...")
    update_scraper_workflow(config)
    update_perda_workflow(config)
    
    print("\n📝 Updating scraper scripts...")
    update_scraper_script(config)
    update_perda_script(config)
    
    # Generate summary
    generate_config_summary(config)
    
    print("\n✅ Configuration sync complete!")
    print("\n💡 Next steps:")
    print("   1. Review changes: git diff")
    print("   2. Commit: git add -A && git commit -m 'Update config'")
    print("   3. Push: git push origin main")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure you have exported config from web interface")
        print("   and placed it in config/portal-config.json")
