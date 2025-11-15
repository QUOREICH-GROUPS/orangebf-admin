import json
import re
from html import unescape

# Charger les données brutes
with open("orange_services.json", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

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
