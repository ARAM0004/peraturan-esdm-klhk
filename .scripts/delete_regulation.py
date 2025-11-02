import json
import os

trigger_path = "trigger/delete_trigger.json"
data_path = "data/regulations.json"

if not os.path.exists(trigger_path):
    print("No trigger file found.")
    exit()

with open(trigger_path, "r") as f:
    trigger = json.load(f)
    delete_id = trigger.get("delete_id")

if not os.path.exists(data_path):
    print("No regulation data found.")
    exit()

with open(data_path, "r") as f:
    data = json.load(f)

# Hapus regulasi sesuai ID
new_data = [r for r in data if r.get("id") != delete_id]

# Simpan kembali
with open(data_path, "w") as f:
    json.dump(new_data, f, indent=2, ensure_ascii=False)

print(f"Deleted regulation with ID: {delete_id}")

# Bersihkan trigger agar tidak berulang
open(trigger_path, "w").close()
