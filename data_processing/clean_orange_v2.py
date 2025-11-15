#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_orange_v2.py - Nettoyage amélioré pour TTS et RAG
Optimise les données pour la synthèse vocale et la qualité RAG
"""

import json
import re
from html import unescape

# Liste de mots-clés pour filtrer le bruit (navigation, footer)
NOISE_KEYWORDS = [
    "Suivez-nous sur", "Facebook", "Instagram", "WhatsApp", "LinkedIn", "YouTube",
    "© Orange", "Mentions légales", "CGU", "Orange.com", "Orange jobs",
    "Boutique en ligne", "Assistance", "Max it",
    "Offres Bons plans Mobile Internet",
    "Carte prépayée VISA",
    "Devenir partenaire",
    "Suivi de commande",
    "Nos boutiques",
    "Aide et contact",
    "Téléphones classiques Téléphones fixes Smartphones Modems",
    "Appels internationaux et Roaming",
    "Précommande SIM en ligne",
    "Divertissements et Loisirs",
    "Prix toutes taxes comprises",
    "Les prix sont affichés",
    "Afficher plus de résultats"
]

def is_noise(text):
    """Détecte si une ligne est du bruit (navigation, footer)"""
    if len(text) < 15:
        return True

    # Vérifier les mots-clés de bruit
    for keyword in NOISE_KEYWORDS:
        if keyword in text:
            return True

    # Détecte les séquences de liens
    if text.count("Voir plus") > 2 or text.count("En savoir plus") > 2:
        return True

    return False

def clean_text_for_tts(text):
    """Nettoie et structure le texte pour TTS"""
    # Décode HTML
    text = unescape(text)

    # Supprime balises HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Supprime le gras/italique markdown (**texte**, __texte__)
    text = text.replace("**", " ").replace("__", " ")

    # Normalise les bullets Markdown / listes
    # Remplace "- item" par une phrase indépendante
    text = re.sub(r"(\s|^)-\s+(?=[A-Za-zÀ-ÿ0-9])", ". ", text)
    # Remplace ": -" (titre suivi de bullet) par ": "
    text = re.sub(r":\s*-\s+", ": ", text)

    # Retire les majuscules collées aux deux-points (SONABEL :... -> SONABEL: ...)
    text = re.sub(r"\s+:\s*", ": ", text)

    # Supprime les doubles espaces créés par les remplacements
    text = re.sub(r"\s+", " ", text).strip()

    # Supprime les shields Markdown restants type `*texte*` (mais préserve *144#)
    text = re.sub(r"\*(?!\d)([^*]+?)\*", r"\1", text)

    # Normalise espaces multiples
    text = re.sub(r"\s+", " ", text).strip()

    # Ajoute points manquants après certains patterns
    # Pattern: minuscule suivie de majuscule sans ponctuation
    text = re.sub(r"([a-zé])\s+([A-ZÀÉÈ])", r"\1. \2", text)

    # Normalise ponctuation
    text = re.sub(r"\s+([,;:!?.])", r"\1", text)
    text = re.sub(r"([,;:!?.])\s*", r"\1 ", text)

    # Remplace "..." par point final
    text = re.sub(r"\.\.\.", ".", text)
    text = re.sub(r"\.\.+", ".", text)

    # Nettoie les espaces autour de la ponctuation
    text = re.sub(r"\s+([,;:!?.])", r"\1", text)
    text = re.sub(r"([,;:!?.])([A-ZÀÉ])", r"\1 \2", text)

    return text.strip()

def split_into_sentences(text):
    """Découpe le texte en phrases pour TTS"""
    # Sépare aux points, points d'exclamation, points d'interrogation
    sentences = re.split(r"(?<=[.!?])\s+", text)

    clean_sentences = []
    for sent in sentences:
        sent = sent.strip()

        # Ignore les phrases vides ou trop courtes
        if len(sent) < 20:
            continue

        # Ignore le bruit
        if is_noise(sent):
            continue

        # Assure qu'il y a une ponctuation finale
        if not sent.endswith((".", "!", "?")):
            sent += "."

        clean_sentences.append(sent)

    return clean_sentences

def extract_meaningful_content(text):
    """Extrait seulement le contenu significatif"""
    # Nettoie le texte
    text = clean_text_for_tts(text)

    # Découpe en phrases
    sentences = split_into_sentences(text)

    # Filtre les phrases qui sont vraiment utiles
    meaningful = []

    for sent in sentences:
        # Ignore les duplications
        if sent in meaningful:
            continue

        # Garde les phrases avec du contenu substantiel
        # (pas juste des titres ou des liens)
        word_count = len(sent.split())
        if word_count >= 5 and word_count <= 100:  # Entre 5 et 100 mots
            meaningful.append(sent)

    return meaningful

# Chargement des données brutes
print("📂 Chargement de orange_services.json...")
data = []

with open("orange_services.json", "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue

        # Extraire l'objet JSON
        start_index = line.find('{')
        end_index = line.rfind('}')

        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = line[start_index:end_index + 1]
            try:
                data.append(json.loads(json_str))
            except json.JSONDecodeError as e:
                print(f"⚠️  Erreur ligne {line_num}: {e}")

print(f"✅ {len(data)} pages chargées")

# Traitement et nettoyage
print("\n🧹 Nettoyage et extraction du contenu significatif...")
cleaned_data = []

for item in data:
    content = item.get("content", "")
    url = item.get("url", "")

    # Extraire les phrases significatives
    sentences = extract_meaningful_content(content)

    # Ajouter chaque phrase comme un document séparé
    for sent in sentences:
        cleaned_data.append({
            "url": url,
            "text": sent
        })

# Suppression des doublons
print("\n🔍 Suppression des doublons...")
unique_texts = set()
unique_data = []

for item in cleaned_data:
    text = item["text"]
    if text not in unique_texts:
        unique_texts.add(text)
        unique_data.append(item)

print(f"✅ {len(unique_data)} paragraphes uniques (avant: {len(cleaned_data)})")

# Sauvegarde du fichier nettoyé
output_file = "orange_services_clean_v2.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(unique_data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Fichier sauvegardé: {output_file}")

# Statistiques
total_chars = sum(len(item["text"]) for item in unique_data)
avg_length = total_chars / len(unique_data) if unique_data else 0

print(f"\n📊 Statistiques:")
print(f"   - Nombre de paragraphes: {len(unique_data)}")
print(f"   - Longueur moyenne: {avg_length:.0f} caractères")
print(f"   - Total caractères: {total_chars:,}")

# Exemples
print(f"\n📝 Exemples de paragraphes nettoyés:")
for i, item in enumerate(unique_data[:5], 1):
    text = item["text"]
    preview = text[:100] + "..." if len(text) > 100 else text
    print(f"   {i}. {preview}")

print(f"\n✅ Nettoyage terminé! Données optimisées pour TTS et RAG.")
