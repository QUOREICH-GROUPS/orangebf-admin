#!/usr/bin/env python3
"""
Script de test TTS - Démo de la synthèse vocale
Teste espeak-ng et simule Piper
"""

import subprocess
import tempfile
from pathlib import Path
import sys

def test_espeak():
    """Test espeak-ng TTS"""
    print("🔊 Test de espeak-ng...")

    text = "Bonjour, je suis votre assistant Orange Burkina Faso. Comment puis-je vous aider?"

    try:
        # Vérifier si espeak-ng est installé
        result = subprocess.run(['which', 'espeak-ng'], capture_output=True)
        if result.returncode != 0:
            print("❌ espeak-ng n'est pas installé")
            print("   Installez-le avec: sudo apt install espeak-ng")
            return False

        # Créer un fichier audio
        output_file = "test_espeak_fr.wav"

        print(f"   Génération de l'audio: {text[:50]}...")
        subprocess.run(
            ['espeak-ng', '-v', 'fr', '-w', output_file, text],
            check=True
        )

        print(f"✅ Audio généré: {output_file}")
        print(f"   Taille: {Path(output_file).stat().st_size} bytes")
        print(f"   Jouez avec: aplay {output_file}")

        # Test en dioula (simulé avec français)
        text_dioula = "I ni ce, Orange Burkina Faso ka dɛmɛbaga tɛ yan"
        output_file_dioula = "test_dioula.wav"

        subprocess.run(
            ['espeak-ng', '-v', 'fr', '-w', output_file_dioula, text_dioula],
            check=True
        )
        print(f"✅ Audio dioula généré: {output_file_dioula}")

        return True

    except FileNotFoundError:
        print("❌ espeak-ng non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_piper_simulation():
    """Simule le test Piper (montre ce qui se passerait)"""
    print("\n🎙️ Simulation Piper-TTS...")
    print("   Sur Pi 5, Piper générerait une voix naturelle de haute qualité")
    print("   Modèle: fr_FR-siwis-medium (48MB)")
    print("   Qualité: ⭐⭐⭐⭐⭐")
    print("   Temps de génération: 0.5-2 secondes")
    print("\n   Commande pour Piper:")
    print('   echo "Texte" | piper --model fr_FR-siwis-medium --output_file output.wav')

def demo_tts_api():
    """Démo de l'utilisation de l'API TTS"""
    print("\n📡 Exemples d'utilisation de l'API TTS:\n")

    print("1️⃣  Question avec audio disponible:")
    print('   curl -X POST http://localhost:8000/ask \\')
    print('     -H "Content-Type: application/json" \\')
    print("     -d '{")
    print('       "question": "Comment activer Orange Money?",')
    print('       "language": "fr",')
    print('       "enable_tts": true')
    print("     }'\n")

    print("2️⃣  Obtenir directement l'audio:")
    print('   curl -X POST http://localhost:8000/speak \\')
    print('     -H "Content-Type: application/json" \\')
    print("     -d '{")
    print('       "question": "Quels sont les forfaits disponibles?",')
    print('       "language": "fr"')
    print("     }' --output response.wav\n")

    print("3️⃣  Convertir du texte en audio:")
    print('   curl "http://localhost:8000/tts?text=Bienvenue&lang=fr" \\')
    print('     --output bienvenue.wav\n')

    print("4️⃣  Avec langues locales:")
    print('   curl -X POST http://localhost:8000/speak \\')
    print('     -H "Content-Type: application/json" \\')
    print("     -d '{")
    print('       "question": "Comment ça va?",')
    print('       "language": "moore"')
    print("     }' --output mooré.wav\n")

def show_architecture():
    """Montre l'architecture du système complet"""
    print("\n🏗️  Architecture du Système RAG + TTS:\n")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  Question de l'utilisateur (texte ou voix)         │")
    print("└────────────────┬────────────────────────────────────┘")
    print("                 │")
    print("                 ▼")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  1. FAISS Retrieval (recherche sémantique)         │")
    print("│     → Top 3 passages pertinents                     │")
    print("│     → Scores: 0.57-0.89                             │")
    print("└────────────────┬────────────────────────────────────┘")
    print("                 │")
    print("                 ▼")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  2. LLM Génération (Phi-3-Mini ou TinyLlama)       │")
    print("│     → Génère la réponse textuelle                   │")
    print("│     → Temps: 3-15 secondes                          │")
    print("└────────────────┬────────────────────────────────────┘")
    print("                 │")
    print("                 ▼")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  3. TTS (Piper ou eSpeak)                          │")
    print("│     → Convertit la réponse en audio                 │")
    print("│     → Format: WAV 22kHz                             │")
    print("│     → Temps: 0.5-2 secondes                         │")
    print("└────────────────┬────────────────────────────────────┘")
    print("                 │")
    print("                 ▼")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  Réponse audio + texte retournée                   │")
    print("│  Format: JSON + WAV file                            │")
    print("└─────────────────────────────────────────────────────┘")
    print("\n📊 Performance totale: 5-20 secondes selon le modèle")

if __name__ == "__main__":
    print("=" * 60)
    print("  🎙️  TEST TTS - Orange Burkina Faso RAG Chatbot")
    print("=" * 60)

    # Test espeak
    espeak_ok = test_espeak()

    # Simulation Piper
    test_piper_simulation()

    # Démo API
    demo_tts_api()

    # Architecture
    show_architecture()

    print("\n" + "=" * 60)
    if espeak_ok:
        print("✅ Tests réussis!")
        print("\n📝 Prochaines étapes:")
        print("   1. Sur Pi 5: installer Piper pour meilleure qualité")
        print("   2. Lancer: uvicorn data_processing.rag_server_tts:app")
        print("   3. Tester avec l'API /speak")
    else:
        print("⚠️  espeak-ng non disponible")
        print("   Sur Pi 5, installez: sudo apt install espeak-ng")
    print("=" * 60)
