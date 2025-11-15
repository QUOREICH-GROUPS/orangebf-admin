# Fonctionnalités Vocales - RAG Orange Burkina Faso

Ce document décrit l'intégration des fonctionnalités vocales OpenAI (Whisper + TTS) dans le chatbot RAG.

## 🎯 Fonctionnalités

Le serveur RAG intègre maintenant trois endpoints vocaux :

1. **`/transcribe`** - Speech-to-Text (Whisper)
2. **`/speak`** - Text-to-Speech
3. **`/voice-chat`** - Chat vocal complet (audio → réponse audio)

## ⚙️ Configuration

### 1. Installer les dépendances

```bash
pip install openai python-dotenv
```

### 2. Configurer la clé API OpenAI

Créez un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditez le fichier `.env` et ajoutez votre clé API OpenAI :

```bash
OPENAI_API_KEY=sk-proj-votre_clé_ici
```

Obtenez votre clé API sur : https://platform.openai.com/api-keys

### 3. Démarrer le serveur

```bash
uvicorn data_processing.rag_server_gpt4all:app --reload
```

Le serveur démarre sur `http://localhost:8000`

## 📡 Utilisation des Endpoints

### 1. `/transcribe` - Transcription audio en texte

**Méthode:** POST
**Content-Type:** multipart/form-data
**Fichiers supportés:** mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB)

**Exemple avec curl:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@question.mp3"
```

**Réponse:**
```json
{
  "text": "Comment activer Orange Money ?",
  "filename": "question.mp3"
}
```

**Exemple Python:**
```python
import requests

with open("question.mp3", "rb") as f:
    files = {"file": ("question.mp3", f, "audio/mpeg")}
    response = requests.post("http://localhost:8000/transcribe", files=files)
    print(response.json()["text"])
```

---

### 2. `/speak` - Conversion texte en audio

**Méthode:** POST
**Content-Type:** application/json
**Retour:** Fichier MP3

**Paramètres:**
- `text` (string, requis) : Le texte à convertir en audio
- `voice` (string, optionnel) : La voix à utiliser (défaut: "nova")
  - Options: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

**Exemple avec curl:**
```bash
curl -X POST "http://localhost:8000/speak" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour, bienvenue chez Orange Burkina Faso", "voice": "nova"}' \
  --output response.mp3
```

**Exemple Python:**
```python
import requests

payload = {
    "text": "Pour activer Orange Money, composez le *144#",
    "voice": "nova"
}

response = requests.post("http://localhost:8000/speak", json=payload)

with open("response.mp3", "wb") as f:
    f.write(response.content)
```

---

### 3. `/voice-chat` - Chat vocal complet

**Méthode:** POST
**Content-Type:** multipart/form-data
**Retour:** Fichier MP3 (réponse audio)

Cet endpoint combine tout le pipeline :
1. Transcrit votre question audio en texte (Whisper)
2. Recherche le contexte pertinent dans la base de données (FAISS)
3. Génère une réponse avec le modèle RAG (GPT4All)
4. Convertit la réponse en audio (OpenAI TTS)

**Headers de réponse:**
- `X-Question-Text` : Votre question transcrite
- `X-Response-Text` : Début de la réponse textuelle (200 premiers caractères)

**Exemple avec curl:**
```bash
curl -X POST "http://localhost:8000/voice-chat" \
  -F "file=@question.mp3" \
  -o chat_response.mp3 \
  -v
```

**Exemple Python:**
```python
import requests

with open("question.mp3", "rb") as f:
    files = {"file": ("question.mp3", f, "audio/mpeg")}
    response = requests.post("http://localhost:8000/voice-chat", files=files)

# Récupérer les informations dans les headers
question = response.headers.get("X-Question-Text")
answer_preview = response.headers.get("X-Response-Text")

print(f"Question: {question}")
print(f"Réponse: {answer_preview}")

# Sauvegarder l'audio
with open("chat_response.mp3", "wb") as f:
    f.write(response.content)
```

---

## 🧪 Script de Test

Un script de test complet est fourni : `test_voice_api.py`

### Exemples d'utilisation

```bash
# Vérifier que le serveur est en ligne
python test_voice_api.py

# Transcrire un fichier audio
python test_voice_api.py --transcribe question.mp3

# Convertir du texte en audio
python test_voice_api.py --speak "Comment activer Orange Money?"

# Choisir une voix différente
python test_voice_api.py --speak "Bonjour" --voice shimmer --output hello.mp3

# Test complet : question audio -> réponse audio
python test_voice_api.py --voice-chat question.mp3 --output reponse.mp3

# Question texte (sans voix)
python test_voice_api.py --ask "Comment activer Orange Money?"
```

---

## 🎭 Voix Disponibles (TTS)

OpenAI propose 6 voix différentes :

| Voix | Description |
|------|-------------|
| `alloy` | Voix neutre et équilibrée |
| `echo` | Voix masculine douce |
| `fable` | Voix narrative britannique |
| `onyx` | Voix masculine profonde |
| `nova` | Voix féminine claire (défaut) |
| `shimmer` | Voix féminine énergique |

Modifiez la constante `TTS_VOICE` dans `rag_server_gpt4all.py` pour changer la voix par défaut.

---

## 💰 Tarification OpenAI

### Whisper (Speech-to-Text)
- **$0.006 / minute** d'audio transcrit

### TTS (Text-to-Speech)
- **TTS Standard** (`tts-1`) : $0.015 / 1K caractères
- **TTS HD** (`tts-1-hd`) : $0.030 / 1K caractères

**Exemple de coût pour `/voice-chat` :**
- Question de 10 secondes : ~$0.001
- Réponse de 100 mots (~500 caractères) : ~$0.008
- **Total : ~$0.009 par interaction vocale complète**

---

## 🔒 Sécurité

- Le fichier `.env` contient vos clés API sensibles
- Il est automatiquement ignoré par git (`.gitignore`)
- **NE JAMAIS** committer le fichier `.env`
- Partagez uniquement `.env.example` avec les autres développeurs

---

## 🛠️ Dépannage

### Erreur : "Service vocal non disponible"
→ Vérifiez que `OPENAI_API_KEY` est définie dans `.env`

### Erreur : "Type de fichier non supporté"
→ Assurez-vous d'envoyer un format audio supporté (mp3, wav, etc.)

### Erreur : "Invalid API key"
→ Vérifiez que votre clé API OpenAI est valide et active

### Le serveur ne trouve pas le fichier .env
→ Assurez-vous que `.env` est à la racine du projet et que `python-dotenv` est installé

---

## 📚 Ressources

- [Documentation OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text)
- [Documentation OpenAI TTS](https://platform.openai.com/docs/guides/text-to-speech)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 🚀 Intégration Frontend

### Exemple HTML/JavaScript simple

```html
<!DOCTYPE html>
<html>
<head>
    <title>Orange Voice Chat</title>
</head>
<body>
    <h1>Chat Vocal Orange</h1>

    <!-- Enregistrement audio -->
    <button id="recordBtn">🎤 Enregistrer</button>
    <button id="stopBtn" disabled>⏹️ Arrêter</button>

    <!-- Lecture de la réponse -->
    <audio id="responseAudio" controls></audio>

    <script>
        let mediaRecorder;
        let audioChunks = [];

        document.getElementById('recordBtn').onclick = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
                audioChunks = [];

                // Envoyer à /voice-chat
                const formData = new FormData();
                formData.append('file', audioBlob, 'question.mp3');

                const response = await fetch('http://localhost:8000/voice-chat', {
                    method: 'POST',
                    body: formData
                });

                const responseBlob = await response.blob();
                const audioUrl = URL.createObjectURL(responseBlob);

                // Lire la réponse
                document.getElementById('responseAudio').src = audioUrl;
            };

            mediaRecorder.start();
            document.getElementById('recordBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        };

        document.getElementById('stopBtn').onclick = () => {
            mediaRecorder.stop();
            document.getElementById('recordBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        };
    </script>
</body>
</html>
```

---

**Développé avec ❤️ pour Orange Burkina Faso**
