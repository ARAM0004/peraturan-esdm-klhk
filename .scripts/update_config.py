#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Config Handler
Membaca trigger/config_update.json dan update config.json
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    trigger_path = Path("trigger/config_update.json")
    config_path = Path("config.json")
    
    # Check trigger exists
    if not trigger_path.exists():
        print("ℹ️  No config update trigger found")
        return
    
    # Load trigger
    try:
        with open(trigger_path, 'r', encoding='utf-8') as f:
            trigger = json.load(f)
    except Exception as e:
        print(f"❌ Error loading trigger: {e}")
        return
    
    # Check if trigger is empty
    if not trigger or trigger.get('action') != 'update_config':
        print("ℹ️  Empty trigger, skipping")
        trigger_path.unlink(missing_ok=True)
        return
    
    print("="*60)
    print("🔧 UPDATING CONFIGURATION")
    print("="*60)
    
    # Load current config
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            print("⚠️  config.json not found, creating new one")
            config = {
                "scraper": {
                    "esdm": {},
                    "klhk": {},
                    "perda": {}
                },
                "general": {}
            }
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Apply updates
    new_config = trigger.get('config', {})
    
    if not new_config:
        print("⚠️  No config data in trigger")
        return
    
    print("\n📝 Applying updates:")
    
    # Update ESDM config
    if 'esdm' in new_config:
        for key, value in new_config['esdm'].items():
            config['scraper']['esdm'][key] = value
            print(f"   ESDM.{key} = {value}")
    
    # Update KLHK config
    if 'klhk' in new_config:
        for key, value in new_config['klhk'].items():
            config['scraper']['klhk'][key] = value
            print(f"   KLHK.{key} = {value}")
    
    # Update Perda config
    if 'perda' in new_config:
        for key, value in new_config['perda'].items():
            config['scraper']['perda'][key] = value
            print(f"   Perda.{key} = {value}")
    
    # Update general config
    if 'general' in new_config:
        for key, value in new_config['general'].items():
            config['general'][key] = value
            print(f"   General.{key} = {value}")
    
    # Add metadata
    config['last_updated'] = datetime.now().isoformat()
    config['updated_by'] = trigger.get('updated_by', 'web_interface')
    
    # Save updated config
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("\n✅ Config updated successfully")
        print(f"💾 Saved to: {config_path}")
    except Exception as e:
        print(f"\n❌ Error saving config: {e}")
        return
    
    # Clear trigger
    try:
        trigger_path.unlink()
        print("🧹 Trigger file cleaned")
    except Exception as e:
        print(f"⚠️  Could not delete trigger: {e}")
    
    print("="*60)

if __name__ == "__main__":
    main()
