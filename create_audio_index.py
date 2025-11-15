#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_audio_index.py - Indexation des fichiers audio MP3
Génère audio_index.json avec métadonnées pour chaque fichier
"""

import os
import json
from pathlib import Path

# Configuration
AUDIO_DIR = "static/audio"
OUTPUT_FILE = "audio_index.json"

# Métadonnées manuelles pour les hymnes nationaux
AUDIO_METADATA = {
    "moore": {
        "transcription": "Hymne national du Burkina Faso en langue Moore (Ditanyé)",
        "langue": "moore",
        "categorie": "hymne_national",
        "tonalite": "solennel",
        "description": "Version officielle de l'hymne national Le Ditanyé en Moore"
    },
    "dioula": {
        "transcription": "Hymne national du Burkina Faso en langue Dioula (Faso Fasa)",
        "langue": "dioula",
        "categorie": "hymne_national",
        "tonalite": "solennel",
        "description": "Version officielle de l'hymne national Le Ditanyé en Dioula"
    },
    "fulfulde": {
        "transcription": "Hymne national du Burkina Faso en langue Fulfulde",
        "langue": "fulfulde",
        "categorie": "hymne_national",
        "tonalite": "solennel",
        "description": "Version officielle de l'hymne national Le Ditanyé en Fulfulde"
    }
}

def create_audio_index():
    """Crée l'index audio à partir du dossier static/audio/"""
    print("=" * 60)
    print("🎵 CRÉATION DE L'INDEX AUDIO")
    print("=" * 60)

    audio_dir = Path(AUDIO_DIR)

    if not audio_dir.exists():
        print(f"❌ Erreur: Le dossier {AUDIO_DIR} n'existe pas!")
        return

    # Scanner les fichiers MP3
    mp3_files = list(audio_dir.glob("*.mp3"))

    # Filtrer les fichiers Zone.Identifier (Windows)
    mp3_files = [f for f in mp3_files if not f.name.endswith(".mp3:Zone.Identifier")]

    print(f"\n📂 Dossier scanné: {AUDIO_DIR}")
    print(f"✅ {len(mp3_files)} fichiers MP3 trouvés")

    # Créer l'index
    audio_index = {}

    for mp3_file in mp3_files:
        # ID basé sur le nom sans extension
        audio_id = mp3_file.stem  # Ex: "moore", "dioula", "fulfulde"

        # Chemin relatif
        relative_path = str(mp3_file)

        # Taille du fichier
        file_size = mp3_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        # Récupérer les métadonnées
        metadata = AUDIO_METADATA.get(audio_id, {
            "transcription": f"Audio {audio_id}",
            "langue": audio_id,
            "categorie": "audio",
            "tonalite": "neutre",
            "description": f"Fichier audio {audio_id}"
        })

        # Créer l'entrée
        audio_index[audio_id] = {
            "id": audio_id,
            "path": relative_path,
            "filename": mp3_file.name,
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
            **metadata
        }

        print(f"\n✅ Indexé: {audio_id}")
        print(f"   Fichier: {mp3_file.name}")
        print(f"   Taille: {file_size_mb:.2f} MB")
        print(f"   Langue: {metadata['langue']}")

    # Sauvegarder l'index
    print(f"\n💾 Sauvegarde de l'index dans {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(audio_index, f, ensure_ascii=False, indent=2)

    print(f"✅ Index créé avec {len(audio_index)} entrées")

    # Afficher un aperçu JSON
    print("\n" + "=" * 60)
    print("📄 APERÇU DE L'INDEX")
    print("=" * 60)
    print(json.dumps(audio_index, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("✅ INDEXATION TERMINÉE!")
    print("=" * 60)
    print(f"Fichier créé: {OUTPUT_FILE}")
    print(f"Utilisable par l'API via /load_audio_index")

if __name__ == "__main__":
    create_audio_index()
