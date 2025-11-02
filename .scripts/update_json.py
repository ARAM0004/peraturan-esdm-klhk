import json
from pathlib import Path

trigger_path = Path("trigger/update.json")
data_path = Path("regulations.json")

if not trigger_path.exists():
    print("❌ Tidak ada file trigger/update.json, workflow berhenti.")
    exit(0)

# --- Baca file trigger ---
with open(trigger_path, "r", encoding="utf-8") as f:
    trigger = json.load(f)

delete_id = trigger.get("delete_id")
delete_keyword = trigger.get("delete_keyword")

if not data_path.exists():
    print("❌ File regulations.json tidak ditemukan.")
    exit(1)

# --- Baca data utama ---
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

updated_published = []

for reg in data.get("published", []):
    if delete_id and reg.get("id") == delete_id:
        print(f"🗑️ Menghapus regulasi ID {delete_id}")
        continue
    if delete_keyword and delete_keyword.lower() in reg.get("title", "").lower():
        print(f"🗑️ Menghapus regulasi dengan keyword: {delete_keyword}")
        continue
    updated_published.append(reg)

# Update data
data["published"] = updated_published
data["lastUpdated"] = trigger.get("timestamp")

# Simpan kembali
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ regulations.json berhasil diperbarui.")

# (Opsional) hapus file trigger agar workflow berikutnya tidak berjalan berulang
trigger_path.unlink(missing_ok=True)
