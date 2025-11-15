#!/usr/bin/env python3
"""
Script de test pour les endpoints vocaux du serveur RAG Orange
"""
import requests
import argparse
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_transcribe(audio_file: str):
    """
    Test de l'endpoint /transcribe
    Envoie un fichier audio et affiche la transcription
    """
    print(f"\n🎤 Test de transcription: {audio_file}")
    print("-" * 50)

    if not Path(audio_file).exists():
        print(f"❌ Fichier introuvable: {audio_file}")
        return

    with open(audio_file, 'rb') as f:
        files = {'file': (Path(audio_file).name, f, 'audio/mpeg')}
        response = requests.post(f"{BASE_URL}/transcribe", files=files)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Transcription réussie!")
        print(f"📝 Texte: {data['text']}")
        print(f"📄 Fichier: {data['filename']}")
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")


def test_speak(text: str, output_file: str = "output.mp3", voice: str = "nova"):
    """
    Test de l'endpoint /speak
    Convertit du texte en audio et sauvegarde le fichier
    """
    print(f"\n🔊 Test de synthèse vocale")
    print("-" * 50)
    print(f"📝 Texte: {text}")
    print(f"🎭 Voix: {voice}")

    payload = {
        "text": text,
        "voice": voice
    }

    response = requests.post(f"{BASE_URL}/speak", json=payload)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"✅ Audio généré avec succès!")
        print(f"💾 Sauvegardé dans: {output_file}")
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")


def test_voice_chat(audio_file: str, output_file: str = "chat_response.mp3"):
    """
    Test de l'endpoint /voice-chat
    Envoie un audio, reçoit une réponse audio du chatbot
    """
    print(f"\n💬 Test de chat vocal complet: {audio_file}")
    print("-" * 50)

    if not Path(audio_file).exists():
        print(f"❌ Fichier introuvable: {audio_file}")
        return

    with open(audio_file, 'rb') as f:
        files = {'file': (Path(audio_file).name, f, 'audio/mpeg')}
        response = requests.post(f"{BASE_URL}/voice-chat", files=files)

    if response.status_code == 200:
        # Récupérer les headers avec les textes
        question_text = response.headers.get('X-Question-Text', 'N/A')
        response_text = response.headers.get('X-Response-Text', 'N/A')

        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"✅ Chat vocal réussi!")
        print(f"❓ Votre question: {question_text}")
        print(f"💡 Début de la réponse: {response_text}")
        print(f"💾 Audio de réponse sauvegardé dans: {output_file}")
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")


def test_ask(question: str):
    """
    Test de l'endpoint /ask (texte seulement, sans voix)
    """
    print(f"\n📩 Test de l'endpoint texte /ask")
    print("-" * 50)
    print(f"❓ Question: {question}")

    payload = {"question": question}
    response = requests.post(f"{BASE_URL}/ask", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Réponse reçue!")
        print(f"💡 Réponse: {data['response']}")
        print(f"\n📚 Passages récupérés ({len(data['retrieved_passages'])}):")
        for i, passage in enumerate(data['retrieved_passages'][:2], 1):
            print(f"  {i}. {passage[:150]}...")
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")


def check_health():
    """Vérifie que le serveur est en ligne"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Serveur en ligne")
            return True
        else:
            print(f"⚠️  Serveur répond avec le code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Serveur non accessible: {e}")
        print(f"💡 Lancez le serveur avec: uvicorn data_processing.rag_server_gpt4all:app --reload")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test des endpoints vocaux du RAG Orange")
    parser.add_argument('--transcribe', type=str, help="Fichier audio à transcrire")
    parser.add_argument('--speak', type=str, help="Texte à convertir en audio")
    parser.add_argument('--voice', type=str, default='nova',
                       help="Voix TTS (alloy, echo, fable, onyx, nova, shimmer)")
    parser.add_argument('--output', type=str, default='output.mp3',
                       help="Fichier de sortie pour l'audio généré")
    parser.add_argument('--voice-chat', type=str, help="Fichier audio pour le chat vocal complet")
    parser.add_argument('--ask', type=str, help="Question texte (sans voix)")
    parser.add_argument('--url', type=str, default='http://localhost:8000',
                       help="URL du serveur (défaut: http://localhost:8000)")

    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.url

    print("=" * 50)
    print("🧪 TEST DES ENDPOINTS VOCAUX - RAG ORANGE")
    print("=" * 50)

    if not check_health():
        sys.exit(1)

    # Si aucune option n'est fournie, afficher l'aide
    if not any([args.transcribe, args.speak, args.voice_chat, args.ask]):
        parser.print_help()
        print("\n📋 Exemples d'utilisation:")
        print("  # Transcrire un audio")
        print("  python test_voice_api.py --transcribe question.mp3")
        print("\n  # Convertir du texte en audio")
        print("  python test_voice_api.py --speak \"Bonjour, comment activer Orange Money?\"")
        print("\n  # Test complet (question audio -> réponse audio)")
        print("  python test_voice_api.py --voice-chat question.mp3")
        print("\n  # Question texte simple")
        print("  python test_voice_api.py --ask \"Comment activer Orange Money?\"")
        sys.exit(0)

    # Exécuter les tests demandés
    if args.transcribe:
        test_transcribe(args.transcribe)

    if args.speak:
        test_speak(args.speak, args.output, args.voice)

    if args.voice_chat:
        test_voice_chat(args.voice_chat, args.output)

    if args.ask:
        test_ask(args.ask)

    print("\n" + "=" * 50)
    print("✅ Tests terminés!")
    print("=" * 50)


if __name__ == "__main__":
    main()
