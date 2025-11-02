#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced update script untuk menangani berbagai aksi dari web interface
Mendukung: approve, delete, add_manual
"""

import json
from pathlib import Path
from datetime import datetime

def load_json(path):
    """Load JSON file dengan error handling"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File {path} tidak ditemukan")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error parsing JSON di {path}")
        return None

def save_json(path, data):
    """Save JSON file dengan formatting"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    trigger_path = Path("trigger/update.json")
    data_path = Path("regulations.json")

    # Check trigger file exists
    if not trigger_path.exists():
        print("ℹ️ Tidak ada file trigger, workflow berhenti.")
        return

    # Load trigger
    trigger = load_json(trigger_path)
    if not trigger:
        return

    # Load main data
    regulations_data = load_json(data_path)
    if not regulations_data:
        regulations_data = {
            'published': [],
            'pending': [],
            'lastUpdated': ''
        }

    # Process action
    action = trigger.get('action', 'delete')  # default untuk backward compatibility
    
    print(f"🔄 Processing action: {action}")

    if action == 'approve':
        # Move regulation from pending to published
        reg_id = trigger.get('regulation_id')
        if reg_id:
            for i, reg in enumerate(regulations_data['pending']):
                if reg['id'] == reg_id:
                    approved_reg = regulations_data['pending'].pop(i)
                    approved_reg['verified'] = True
                    approved_reg['publishedDate'] = datetime.now().isoformat()
                    regulations_data['published'].insert(0, approved_reg)
                    print(f"✅ Approved: {approved_reg['number']}")
                    break

    elif action == 'add_manual':
        # Add manual regulation
        new_reg = trigger.get('regulation')
        if new_reg:
            regulations_data['published'].insert(0, new_reg)
            print(f"✅ Added manual regulation: {new_reg['number']}")

    elif action == 'delete' or trigger.get('delete_id'):
        # Delete regulation (support old and new format)
        delete_id = trigger.get('delete_id') or trigger.get('regulation_id')
        if delete_id:
            # Try to delete from published
            initial_count = len(regulations_data['published'])
            regulations_data['published'] = [
                r for r in regulations_data['published'] 
                if r.get('id') != delete_id
            ]
            
            if len(regulations_data['published']) < initial_count:
                print(f"🗑️ Deleted regulation ID: {delete_id}")
            
            # Also try to delete from pending
            regulations_data['pending'] = [
                r for r in regulations_data['pending'] 
                if r.get('id') != delete_id
            ]

    # Update timestamp
    regulations_data['lastUpdated'] = trigger.get('timestamp', datetime.now().isoformat())

    # Save updated data
    save_json(data_path, regulations_data)
    print("✅ regulations.json berhasil diperbarui")

    # Clear trigger file
    try:
        trigger_path.unlink()
        print("🧹 Trigger file dibersihkan")
    except Exception as e:
        print(f"⚠️ Warning: Tidak bisa menghapus trigger file: {e}")

if __name__ == "__main__":
    main()
