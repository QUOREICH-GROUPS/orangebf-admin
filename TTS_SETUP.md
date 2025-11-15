# Guide d'Installation - Synthèse Vocale (TTS)

## 🎙️ Deux Options TTS pour Raspberry Pi 5

### Option 1: Piper-TTS ⭐ **RECOMMANDÉ**
- **Qualité**: ⭐⭐⭐⭐⭐ (Voix naturelle, excellente)
- **Vitesse**: ⚡⚡⚡⚡ (0.5-2 secondes pour une phrase)
- **RAM**: ~200-300 MB
- **Langues**: Français (natif), autres via espeak
- **Offline**: ✅ 100% local
- **Développé par**: Rhasspy (open-source)

### Option 2: eSpeak-NG (Fallback)
- **Qualité**: ⭐⭐⭐ (Voix robotique mais claire)
- **Vitesse**: ⚡⚡⚡⚡⚡ (instantané)
- **RAM**: ~50 MB
- **Langues**: 100+ langues (dont français, mais pas mooré/dioula natifs)
- **Offline**: ✅ 100% local
- **Avantage**: Déjà installé sur la plupart des systèmes

---

## 📦 Installation Rapide

### Sur Raspberry Pi 5 (Raspberry Pi OS):

```bash
# 1. Installer espeak-ng (rapide, toujours utile comme fallback)
sudo apt update
sudo apt install -y espeak-ng

# 2. Installer Piper-TTS (pour la meilleure qualité)
# Télécharger le binaire ARM64
cd /tmp
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz

# Copier vers /usr/local/bin
sudo cp piper/piper /usr/local/bin/
sudo chmod +x /usr/local/bin/piper

# Vérifier l'installation
piper --version
espeak-ng --version

# 3. Télécharger les modèles de voix français
mkdir -p ~/piper_models
cd ~/piper_models

# Modèle français medium (recommandé - 48MB)
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json

# Ou modèle low (plus rapide - 20MB)
# wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx
# wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx.json

# 4. Configurer le chemin des modèles
export PIPER_MODEL_DIR=~/piper_models
echo 'export PIPER_MODEL_DIR=~/piper_models' >> ~/.bashrc
```

---

## 🧪 Test des Moteurs TTS

### Test espeak-ng:
```bash
# En français
espeak-ng -v fr "Bonjour, je suis votre assistant Orange Burkina Faso"

# Sauvegarder en WAV
espeak-ng -v fr -w test_espeak.wav "Ceci est un test"

# Écouter le fichier
aplay test_espeak.wav
```

### Test Piper:
```bash
# Test avec Piper
echo "Bonjour, je suis votre assistant Orange Burkina Faso" | \
  piper --model ~/piper_models/fr_FR-siwis-medium --output_file test_piper.wav

# Écouter
aplay test_piper.wav
```

---

## 🚀 Lancer le Serveur avec TTS

```bash
cd /home/suprox/Projet/Laravel/ai/orangebf
source venv/bin/activate

# Lancer le serveur TTS
uvicorn data_processing.rag_server_tts:app --host 0.0.0.0 --port 8000
```

---

## 🎯 Utilisation - Exemples API

### 1. Question avec réponse texte + audio disponible
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment activer Orange Money?",
    "language": "fr",
    "enable_tts": true
  }'
```

**Réponse:**
```json
{
  "question": "Comment activer Orange Money?",
  "response": "Pour activer Orange Money...",
  "language": "fr",
  "audio_url": "/tts?text=Pour activer Orange Money...&lang=fr",
  "audio_available": true
}
```

### 2. Obtenir directement l'audio d'une réponse
```bash
curl -X POST http://localhost:8000/speak \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les forfaits disponibles?",
    "language": "fr"
  }' \
  --output response.wav

# Écouter
aplay response.wav
```

### 3. Convertir du texte en audio (TTS standalone)
```bash
# Obtenir l'audio d'un texte
curl "http://localhost:8000/tts?text=Bienvenue%20chez%20Orange&lang=fr" \
  --output bienvenue.wav

aplay bienvenue.wav
```

### 4. Lister les voix disponibles
```bash
curl http://localhost:8000/voices
```

---

## 🌍 Support des Langues Locales

### Statut Actuel:

| Langue | Moteur | Qualité | Statut |
|--------|--------|---------|--------|
| **Français** | Piper + espeak | ⭐⭐⭐⭐⭐ | ✅ Natif |
| **Mooré** | espeak (via fr) | ⭐⭐ | ⚠️ Fallback |
| **Dioula** | espeak (via fr) | ⭐⭐ | ⚠️ Fallback |
| **Fulfulde** | espeak (via fr) | ⭐⭐ | ⚠️ Fallback |

### Pour Améliorer les Langues Locales:

**Option 1: Entraîner un modèle Piper personnalisé**
- Nécessite: ~10 heures d'enregistrements audio en mooré/dioula
- Qualité finale: ⭐⭐⭐⭐⭐
- Temps de formation: 2-3 jours sur GPU
- Guide: https://github.com/rhasspy/piper/blob/master/TRAINING.md

**Option 2: Utiliser Coqui XTTS (plus lourd)**
- Supporte le voice cloning
- Peut adapter une voix française au mooré/dioula
- RAM nécessaire: ~4-6 GB
- Plus lent mais meilleure qualité

**Option 3: Contribuer à espeak-ng**
- Ajouter la phonétique mooré/dioula à espeak
- Guide: https://github.com/espeak-ng/espeak-ng/blob/master/docs/add_language.md

---

## 🎨 Interface Web Simple (HTML + JavaScript)

Créer un fichier `static/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Orange Burkina Faso - Assistant Vocal</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        #question { width: 100%; padding: 10px; font-size: 16px; }
        button { padding: 10px 20px; font-size: 16px; margin: 10px 5px; cursor: pointer; }
        #response { margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
        .loading { color: #ff7900; }
    </style>
</head>
<body>
    <h1>🍊 Assistant Vocal Orange Burkina Faso</h1>

    <input type="text" id="question" placeholder="Posez votre question...">
    <br>

    <label>Langue:</label>
    <select id="language">
        <option value="fr">Français</option>
        <option value="moore">Mooré</option>
        <option value="dioula">Dioula</option>
    </select>

    <br>
    <button onclick="askQuestion()">📝 Envoyer</button>
    <button onclick="askAndSpeak()">🔊 Envoyer et Parler</button>

    <div id="response"></div>
    <audio id="audio" controls style="width: 100%; margin-top: 10px; display: none;"></audio>

    <script>
        async function askQuestion() {
            const question = document.getElementById('question').value;
            const language = document.getElementById('language').value;
            const responseDiv = document.getElementById('response');

            responseDiv.innerHTML = '<p class="loading">⏳ Recherche en cours...</p>';

            const response = await fetch('http://localhost:8000/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    language: language,
                    enable_tts: true
                })
            });

            const data = await response.json();
            responseDiv.innerHTML = `
                <h3>Question:</h3>
                <p>${data.question}</p>
                <h3>Réponse:</h3>
                <p>${data.response}</p>
            `;
        }

        async function askAndSpeak() {
            const question = document.getElementById('question').value;
            const language = document.getElementById('language').value;
            const responseDiv = document.getElementById('response');
            const audioElement = document.getElementById('audio');

            responseDiv.innerHTML = '<p class="loading">⏳ Génération de la réponse...</p>';

            const response = await fetch('http://localhost:8000/speak', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    language: language
                })
            });

            const audioBlob = await response.blob();
            const responseText = response.headers.get('X-Response-Text');

            responseDiv.innerHTML = `
                <h3>Question:</h3>
                <p>${question}</p>
                <h3>Réponse:</h3>
                <p>${responseText}</p>
            `;

            // Jouer l'audio
            const audioUrl = URL.createObjectURL(audioBlob);
            audioElement.src = audioUrl;
            audioElement.style.display = 'block';
            audioElement.play();
        }

        // Permettre Entrée pour envoyer
        document.getElementById('question').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') askQuestion();
        });
    </script>
</body>
</html>
```

Servir avec:
```bash
# Ajouter CORS au serveur
pip install fastapi-cors

# Ou utiliser un serveur HTTP simple
cd static
python3 -m http.server 8080
# Ouvrir http://localhost:8080
```

---

## 📊 Performances TTS sur Pi 5

### Piper (fr_FR-siwis-medium):
- Temps de génération: 0.5-2 secondes pour 50 mots
- RAM utilisée: ~250 MB
- CPU: ~80% pendant la génération
- Qualité audio: ⭐⭐⭐⭐⭐

### eSpeak-ng:
- Temps de génération: <0.1 seconde
- RAM utilisée: ~50 MB
- CPU: ~20%
- Qualité audio: ⭐⭐⭐

### Temps Total (Question → Réponse vocale):
```
Avec TinyLlama + Piper:
  - FAISS retrieval: ~0.3s
  - LLM génération: ~3-6s
  - TTS Piper: ~1-2s
  - TOTAL: ~5-9 secondes ✅

Avec Phi-3-Mini + Piper:
  - FAISS retrieval: ~0.3s
  - LLM génération: ~8-15s
  - TTS Piper: ~1-2s
  - TOTAL: ~10-18 secondes ✅
```

---

## 🔧 Configuration Avancée

### Changer le moteur TTS dans le code:
```python
# Dans rag_server_tts.py, ligne 20:
TTS_ENGINE = "piper"  # ou "espeak"
```

### Ajuster la qualité Piper:
```python
# Utiliser le modèle low (plus rapide)
PIPER_MODEL = "fr_FR-siwis-low"

# Ou high (meilleure qualité, plus lent)
PIPER_MODEL = "fr_FR-siwis-high"
```

---

## 🎤 Prochaines Étapes - Reconnaissance Vocale (STT)

Pour un assistant vocal complet, ajouter la reconnaissance vocale:

**Options Open Source:**
1. **Vosk** - Offline, supporte le français, léger
2. **Whisper (OpenAI)** - Excellente qualité, peut tourner sur Pi 5
3. **Coqui STT** - Open source, nécessite entraînement

Cela permettra:
```
Utilisateur parle → [STT] → Texte → [RAG] → Réponse → [TTS] → Audio
```

Guide complet STT à venir! 🎙️

---

## 📚 Resources

- Piper TTS: https://github.com/rhasspy/piper
- Modèles de voix: https://huggingface.co/rhasspy/piper-voices
- eSpeak-ng: https://github.com/espeak-ng/espeak-ng
- Training Piper: https://github.com/rhasspy/piper/blob/master/TRAINING.md

---

## ✅ Checklist d'Installation

- [ ] espeak-ng installé et testé
- [ ] Piper téléchargé et installé
- [ ] Modèle vocal français téléchargé
- [ ] Serveur TTS lancé
- [ ] Test avec `/tts` endpoint
- [ ] Test avec `/speak` endpoint
- [ ] Interface web fonctionnelle (optionnel)
