# Guide d'Installation - Reconnaissance Vocale (STT)

## 🎤 Trois Options STT pour Raspberry Pi 5

### Comparaison Rapide

| Moteur | Qualité | Vitesse | RAM | Langues | Recommandé Pour |
|--------|---------|---------|-----|---------|-----------------|
| **Whisper Tiny** | ⭐⭐⭐⭐ | ⚡⚡⚡ | ~1GB | 99+ | **Production** |
| **Faster-Whisper** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | ~800MB | 99+ | **Meilleur choix** |
| **Vosk** | ⭐⭐⭐ | ⚡⚡⚡⚡⚡ | ~200MB | Limité | Ressources faibles |

---

## 📦 Option 1: Faster-Whisper ⭐ **RECOMMANDÉ**

Whisper optimisé avec CTranslate2, **4x plus rapide** que Whisper standard!

### Avantages:
- ✅ Excellente qualité (même niveau que Whisper)
- ✅ 4x plus rapide que Whisper standard
- ✅ Moins de RAM (~800MB vs ~1.5GB)
- ✅ 99+ langues dont français
- ✅ Fonctionne très bien sur Pi 5

### Installation:

```bash
source venv/bin/activate

# Installer faster-whisper
pip install faster-whisper

# Test rapide
python3 -c "
from faster_whisper import WhisperModel
print('✅ Faster-Whisper installé')
model = WhisperModel('tiny', device='cpu', compute_type='int8')
print('✅ Modèle tiny chargé')
"
```

### Modèles disponibles:

| Modèle | Taille | RAM | Vitesse | Qualité |
|--------|--------|-----|---------|---------|
| **tiny** | 75 MB | ~800 MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| **base** | 145 MB | ~1 GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| **small** | 488 MB | ~2 GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ |

**Recommandation Pi 5**: Utilisez **tiny** (rapide, bonne qualité)

### Test:

```bash
# Créer un fichier audio de test
espeak-ng -v fr -w test_question.wav "Comment activer Orange Money ?"

# Transcrire avec faster-whisper
python3 << 'EOF'
from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe("test_question.wav", language="fr")

text = " ".join([segment.text for segment in segments])
print(f"Texte transcrit: {text}")
EOF
```

---

## 📦 Option 2: OpenAI Whisper (Standard)

Le modèle original d'OpenAI, très bonne qualité mais plus lent.

### Installation:

```bash
source venv/bin/activate

# Installer whisper
pip install openai-whisper

# Dépendances supplémentaires
sudo apt install ffmpeg

# Test
python3 -c "
import whisper
model = whisper.load_model('tiny')
print('✅ Whisper installé et prêt')
"
```

### Test:

```bash
python3 << 'EOF'
import whisper

model = whisper.load_model("tiny")
result = model.transcribe("test_question.wav", language="fr")
print(f"Texte: {result['text']}")
EOF
```

**Note**: Plus lent que faster-whisper, préférez faster-whisper!

---

## 📦 Option 3: Vosk (Ultra-Léger)

Très rapide mais qualité inférieure, idéal si RAM limitée.

### Installation:

```bash
source venv/bin/activate

# Installer vosk
pip install vosk

# Télécharger le modèle français
mkdir -p models
cd models

# Modèle small français (42MB)
wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
unzip vosk-model-small-fr-0.22.zip
rm vosk-model-small-fr-0.22.zip

cd ..
```

### Test:

```bash
python3 << 'EOF'
from vosk import Model, KaldiRecognizer
import wave
import json

model = Model("models/vosk-model-small-fr-0.22")
wf = wave.open("test_question.wav", "rb")
rec = KaldiRecognizer(model, wf.getframerate())

results = []
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        results.append(result.get("text", ""))

final = json.loads(rec.FinalResult())
results.append(final.get("text", ""))

print(f"Texte: {' '.join(results)}")
EOF
```

---

## 🚀 Lancer l'Assistant Vocal Complet

### Configurer le moteur STT:

Éditer `data_processing/rag_server_voice.py` ligne 21:
```python
STT_ENGINE = "faster-whisper"  # ou "whisper" ou "vosk"
WHISPER_MODEL = "tiny"  # tiny, base, ou small
```

### Démarrer le serveur:

```bash
source venv/bin/activate

# Arrêter les anciens serveurs
pkill -f uvicorn

# Lancer le serveur vocal
uvicorn data_processing.rag_server_voice:app --host 0.0.0.0 --port 8000
```

---

## 🎯 Utilisation - Exemples API

### 1. Question Vocale → Réponse Vocale

```bash
# Enregistrer une question (avec votre micro)
arecord -f cd -d 5 ma_question.wav

# Ou utiliser un fichier de test
espeak-ng -v fr -w ma_question.wav "Quels sont les forfaits internet disponibles?"

# Envoyer au serveur
curl -X POST http://localhost:8000/voice/ask \
  -F "audio=@ma_question.wav" \
  -F "language=fr" \
  -F "response_format=audio" \
  --output reponse.wav

# Écouter la réponse
aplay reponse.wav
```

### 2. Question Vocale → Réponse Texte + Audio

```bash
curl -X POST http://localhost:8000/voice/ask \
  -F "audio=@ma_question.wav" \
  -F "language=fr" \
  -F "response_format=both" \
  | python3 -m json.tool
```

**Réponse:**
```json
{
  "question": "Quels sont les forfaits internet disponibles?",
  "response": "Les forfaits internet disponibles sont...",
  "language": "fr",
  "scores": [0.76, 0.74, 0.73],
  "audio_base64": "UklGRi4gAABXQVZF...",
  "audio_download_url": "/tts?text=..."
}
```

### 3. Transcription Seulement (STT)

```bash
curl -X POST http://localhost:8000/voice/transcribe \
  -F "audio=@ma_question.wav" \
  -F "language=fr"
```

**Réponse:**
```json
{
  "text": "Quels sont les forfaits internet disponibles?",
  "language": "fr",
  "engine": "faster-whisper"
}
```

### 4. Question Texte (mode classique)

```bash
curl -X POST http://localhost:8000/text/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment activer Orange Money?",
    "language": "fr",
    "enable_voice": true
  }'
```

---

## 🎨 Interface Web avec Enregistrement Vocal

Créer `static/voice_assistant.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Assistant Vocal Orange</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #ff7900 0%, #ff9500 100%);
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        h1 { color: #ff7900; text-align: center; }
        button {
            padding: 15px 30px;
            font-size: 18px;
            margin: 10px;
            cursor: pointer;
            border-radius: 8px;
            border: none;
            background: #ff7900;
            color: white;
            transition: 0.3s;
        }
        button:hover { background: #ff9500; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        #recordBtn.recording {
            background: #dc3545;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        #status {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            min-height: 50px;
        }
        #response {
            margin-top: 20px;
            padding: 20px;
            background: #e8f5e9;
            border-radius: 8px;
            display: none;
        }
        audio {
            width: 100%;
            margin-top: 15px;
        }
        .controls {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍊 Assistant Vocal Orange Burkina Faso</h1>

        <div class="controls">
            <button id="recordBtn">🎤 Enregistrer Question</button>
            <button id="stopBtn" disabled>⏹️ Arrêter</button>
            <br>
            <label>Langue:</label>
            <select id="language">
                <option value="fr">Français</option>
                <option value="moore">Mooré</option>
                <option value="dioula">Dioula</option>
            </select>
        </div>

        <div id="status">💡 Cliquez sur "Enregistrer" pour poser une question vocale</div>
        <div id="response"></div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];

        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDiv = document.getElementById('status');
        const responseDiv = document.getElementById('response');
        const languageSelect = document.getElementById('language');

        recordBtn.onclick = async () => {
            audioChunks = [];

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (e) => {
                audioChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendAudio(audioBlob);
            };

            mediaRecorder.start();

            recordBtn.disabled = true;
            recordBtn.classList.add('recording');
            stopBtn.disabled = false;
            statusDiv.innerHTML = '🎤 Enregistrement en cours... Parlez maintenant!';
        };

        stopBtn.onclick = () => {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());

            recordBtn.disabled = false;
            recordBtn.classList.remove('recording');
            stopBtn.disabled = true;
            statusDiv.innerHTML = '⏳ Traitement de votre question...';
        };

        async function sendAudio(audioBlob) {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'question.wav');
            formData.append('language', languageSelect.value);
            formData.append('response_format', 'both');

            try {
                const response = await fetch('http://localhost:8000/voice/ask', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                statusDiv.innerHTML = `
                    <strong>Question détectée:</strong> ${data.question}
                `;

                responseDiv.innerHTML = `
                    <h3>Réponse:</h3>
                    <p>${data.response}</p>
                    <audio controls autoplay>
                        <source src="data:audio/wav;base64,${data.audio_base64}" type="audio/wav">
                    </audio>
                `;
                responseDiv.style.display = 'block';

            } catch (error) {
                statusDiv.innerHTML = `❌ Erreur: ${error.message}`;
                responseDiv.style.display = 'none';
            }
        }
    </script>
</body>
</html>
```

### Utiliser l'interface:

```bash
# Option 1: Servir avec Python
cd static
python3 -m http.server 8080

# Option 2: Ajouter CORS au serveur
# Voir instructions ci-dessous

# Ouvrir dans le navigateur
# http://localhost:8080/voice_assistant.html
```

---

## 🔧 Configuration CORS (pour interface web)

Ajouter CORS à `rag_server_voice.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

# Après app = FastAPI(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Puis:
```bash
pip install fastapi[standard]  # Inclut CORS
```

---

## 📊 Performances sur Raspberry Pi 5

### Avec Faster-Whisper (tiny) + TinyLlama + eSpeak:

```
Pipeline complet (Voice → Voice):
┌────────────────────────────────┐
│ 1. STT (Faster-Whisper tiny)   │  ~2-4 secondes
│ 2. FAISS Retrieval             │  ~0.3 secondes
│ 3. LLM (TinyLlama)             │  ~3-6 secondes
│ 4. TTS (eSpeak)                │  ~0.1 secondes
└────────────────────────────────┘
TOTAL: ~6-11 secondes ✅
```

### Avec Faster-Whisper (tiny) + Phi-3-Mini + Piper:

```
Pipeline complet (Voice → Voice):
┌────────────────────────────────┐
│ 1. STT (Faster-Whisper tiny)   │  ~2-4 secondes
│ 2. FAISS Retrieval             │  ~0.3 secondes
│ 3. LLM (Phi-3-Mini)            │  ~10-15 secondes
│ 4. TTS (Piper)                 │  ~1-2 secondes
└────────────────────────────────┘
TOTAL: ~14-22 secondes ✅
```

**Performance acceptable pour un assistant vocal!**

---

## 🌍 Support Langues Locales (Mooré/Dioula)

### Statut Actuel:

- **STT**: Faster-Whisper transcrit en français (pas de modèle mooré/dioula natif)
- **LLM**: Comprend le contexte mais répond en français
- **TTS**: Utilise voix française

### Pour Améliorer:

1. **Fine-tuner Whisper** sur des audios en mooré/dioula
2. **Entraîner un modèle LLM** bilingue français-mooré
3. **Créer des voix TTS** personnalisées avec Piper

**Resources nécessaires**:
- 10-20 heures d'audio transcrit par langue
- GPU pour l'entraînement (ou cloud)
- 1-2 semaines de travail

---

## 🎙️ Enregistrement Audio sur Pi 5

### Avec USB Microphone:

```bash
# Lister les devices audio
arecord -l

# Enregistrer 5 secondes
arecord -f cd -d 5 question.wav

# Enregistrer avec device spécifique
arecord -D plughw:1,0 -f cd -d 5 question.wav
```

### Avec Microphone intégré (si disponible):

```bash
# Configurer le micro par défaut
nano ~/.asoundrc

# Ajouter:
pcm.!default {
    type asym
    playback.pcm "plughw:0,0"
    capture.pcm "plughw:1,0"
}
```

---

## ✅ Checklist d'Installation STT

- [ ] Faster-Whisper installé et testé
- [ ] Modèle `tiny` téléchargé (automatique au premier usage)
- [ ] Test de transcription réussi
- [ ] Serveur vocal lancé (`rag_server_voice.py`)
- [ ] Test endpoint `/voice/ask`
- [ ] Test endpoint `/voice/transcribe`
- [ ] Interface web fonctionnelle (optionnel)
- [ ] Microphone configuré sur Pi 5

---

## 🚀 Prochaines Étapes

1. **Tester sur Pi 5** avec microphone USB
2. **Optimiser les modèles** (choisir tiny/base/small selon besoins)
3. **Créer des raccourcis vocaux** ("Orange" pour activer)
4. **Intégrer wake word detection** (Porcupine, Snowboy)
5. **Ajouter analytics** (logging des questions)

---

## 📚 Ressources

- Faster-Whisper: https://github.com/guillaumekln/faster-whisper
- OpenAI Whisper: https://github.com/openai/whisper
- Vosk: https://alphacephei.com/vosk/
- Modèles Vosk: https://alphacephei.com/vosk/models
- Fine-tuning Whisper: https://huggingface.co/blog/fine-tune-whisper

---

**Votre assistant vocal est maintenant complet! 🎉**

Parole → Texte → RAG → Réponse → Parole
