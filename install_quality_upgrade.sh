#!/bin/bash
# Script d'installation Piper-TTS + Phi-3-Mini

echo "========================================="
echo "🚀 AMÉLIORATION QUALITÉ - Installation"
echo "========================================="
echo ""

# 1. Installer Piper-TTS
echo "📦 Étape 1/2: Installation de Piper-TTS..."
echo ""

# Vérifier l'architecture
ARCH=$(uname -m)
echo "Architecture détectée: $ARCH"

if [ "$ARCH" = "x86_64" ]; then
    PIPER_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz"
    echo "Téléchargement de Piper pour x86_64..."
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    PIPER_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz"
    echo "Téléchargement de Piper pour ARM64..."
else
    echo "❌ Architecture non supportée: $ARCH"
    exit 1
fi

# Télécharger et installer Piper
cd /tmp
wget -c $PIPER_URL -O piper.tar.gz
tar -xzf piper.tar.gz

# Installer dans /usr/local/bin
sudo cp piper/piper /usr/local/bin/ 2>/dev/null || cp piper/piper ~/bin/
sudo chmod +x /usr/local/bin/piper 2>/dev/null || chmod +x ~/bin/piper

# Vérifier l'installation
if command -v piper &> /dev/null; then
    echo "✅ Piper installé avec succès!"
    piper --version
else
    echo "⚠️  Piper installé dans ~/bin/piper"
fi

# 2. Télécharger le modèle vocal français
echo ""
echo "📥 Téléchargement du modèle vocal français (Siwis Medium - 48MB)..."
cd ~/Projet/Laravel/ai/orangebf
mkdir -p piper_models
cd piper_models

wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json

echo "✅ Modèle vocal français téléchargé!"

# 3. Télécharger Phi-3-Mini
echo ""
echo "📦 Étape 2/2: Téléchargement de Phi-3-Mini (2.3 GB)..."
echo "⏳ Cela peut prendre 5-10 minutes selon votre connexion..."
cd ~/Projet/Laravel/ai/orangebf

wget -c https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

echo "✅ Phi-3-Mini téléchargé!"

# 4. Test Piper
echo ""
echo "🧪 Test de Piper-TTS..."
echo "Bonjour, je suis votre nouvel assistant Orange avec une voix naturelle." | \
    piper --model ~/Projet/Laravel/ai/orangebf/piper_models/fr_FR-siwis-medium \
    --output_file ~/Projet/Laravel/ai/orangebf/test_piper_upgrade.wav

if [ -f ~/Projet/Laravel/ai/orangebf/test_piper_upgrade.wav ]; then
    echo "✅ Test Piper réussi! Fichier: test_piper_upgrade.wav"
else
    echo "⚠️  Test Piper échoué"
fi

# Résumé
echo ""
echo "========================================="
echo "✅ INSTALLATION TERMINÉE!"
echo "========================================="
echo ""
echo "📊 Ce qui a été installé:"
echo "   ✅ Piper-TTS (voix naturelle française)"
echo "   ✅ Modèle fr_FR-siwis-medium (48 MB)"
echo "   ✅ Phi-3-Mini LLM (2.3 GB)"
echo ""
echo "🔧 Prochaine étape:"
echo "   Mettre à jour la configuration du serveur"
echo ""
echo "========================================="
