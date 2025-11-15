import json
import re
from html import unescape

data = []

# Charger les données brutes
with open("orange_services.json", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue

        # Try to find the JSON object within the line
        start_index = line.find('{')
        end_index = line.rfind('}')

        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = line[start_index : end_index + 1]
            try:
                data.append(json.loads(json_str))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from line {line_num} (extracted: '{json_str}'): {e}")
        else:
            print(f"Could not find a valid JSON object in line {line_num}: {line}")

cleaned_data = []

for item in data:
    text = item.get("content", "")

    # Décode les entités HTML (&amp; &quot; etc.)
    text = unescape(text)

    # Supprime les balises HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Supprime les multiples espaces et retour à la ligne
    text = re.sub(r"\s+", " ", text).strip()

    # Ajoute si texte non vide
    if text:
        cleaned_data.append({
            "url": item.get("url"),
            "text": text
        })

# Sauvegarder le fichier nettoyé
with open("orange_services_clean.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

print(f"Nettoyé {len(cleaned_data)} pages.")
