import json
import re

with open("orange_services_clean.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

paragraphs = []

for page in pages:
    text = page["text"]
    # Découpe en paragraphes via les points ou retours à la ligne
    splits = re.split(r'(?<=[.!?])\s+', text)
    for i, para in enumerate(splits):
        para = para.strip()
        if para:
            paragraphs.append({
                "url": page["url"],
                "paragraph_id": i + 1,
                "text": para
            })

# Sauvegarde
with open("orange_services_paragraphs.json", "w", encoding="utf-8") as f:
    json.dump(paragraphs, f, ensure_ascii=False, indent=2)

print(f"Découpé en {len(paragraphs)} paragraphes.")
