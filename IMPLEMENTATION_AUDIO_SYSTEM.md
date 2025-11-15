# 🎵 IMPLÉMENTATION SYSTÈME AUDIO HYBRIDE - GUIDE COMPLET

## ✅ PHASE 1: INDEX AUDIO - **TERMINÉE**

### Fichiers créés:
- ✅ `create_audio_index.py` - Script d'indexation
- ✅ `audio_index.json` - Index avec 3 hymnes (Moore, Dioula, Fulfulde)

---

## 🔧 PHASE 2: INTÉGRATION API FASTAPI

### 2.1 Modifications dans `data_processing/rag_server_voice.py`

**Ajouter après les imports (ligne ~18):**
```python
# Charger l'index audio
AUDIO_INDEX_FILE = "audio_index.json"
audio_map = {}  # Variable globale pour stocker l'index

def load_audio_index():
    """Charge l'index audio depuis audio_index.json"""
    global audio_map
    try:
        if Path(AUDIO_INDEX_FILE).exists():
            with open(AUDIO_INDEX_FILE, "r", encoding="utf-8") as f:
                audio_map = json.load(f)
            print(f"✅ Index audio chargé: {len(audio_map)} fichiers")
            for audio_id, data in audio_map.items():
                print(f"   - {audio_id}: {data['filename']} ({data['size_mb']} MB)")
        else:
            print(f"⚠️ Fichier {AUDIO_INDEX_FILE} non trouvé")
    except Exception as e:
        print(f"❌ Erreur chargement audio_index: {e}")

# Charger l'index au démarrage
load_audio_index()
```

### 2.2 Route pour servir les fichiers audio

**Ajouter après les endpoints existants:**
```python
from fastapi.responses import FileResponse

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """
    Sert les fichiers audio MP3
    Usage: GET /audio/moore.mp3
    """
    audio_path = Path(f"static/audio/{filename}")

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Fichier audio non trouvé")

    return FileResponse(
        str(audio_path),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Accept-Ranges": "bytes"
        }
    )

@app.post("/load_audio_index")
async def reload_audio_index():
    """
    Recharge l'index audio
    Usage: POST /load_audio_index
    """
    load_audio_index()
    return {
        "status": "success",
        "message": f"Index rechargé: {len(audio_map)} fichiers",
        "audio_files": list(audio_map.keys())
    }

@app.get("/audio_index")
async def get_audio_index():
    """
    Retourne l'index audio complet
    Usage: GET /audio_index
    """
    return {
        "count": len(audio_map),
        "files": audio_map
    }
```

### 2.3 Modifier le pipeline RAG (fonction `generate_response`)

**Remplacer la section des connaissances locales par:**
```python
def generate_response(question: str, passages: list, language: str = "fr"):
    """Génère une réponse en utilisant Groq API avec contexte RAG"""

    # VÉRIFIER D'ABORD LES CONNAISSANCES LOCALES
    q_lower = question.lower()

    # 1. Hymne National (Ditanyé) - RETOURNER AUDIO
    if any(word in q_lower for word in ["hymne", "ditanyé", "ditanye", "chante", "chanson nationale"]):
        # Déterminer la langue
        audio_id = language if language in ["moore", "dioula", "fulfulde"] else "moore"

        # Vérifier si audio disponible
        if audio_id in audio_map:
            audio_info = audio_map[audio_id]
            return {
                "type": "audio",
                "audio_url": f"/audio/{audio_info['filename']}",
                "audio_id": audio_id,
                "transcription": audio_info['transcription'],
                "description": audio_info['description'],
                "text": f"🎵 Voici l'hymne national du Burkina Faso en {audio_info['langue']}."
            }
        else:
            # Fallback texte
            hymne_data = local_facts["hymne"]
            if language in hymne_data:
                return {"type": "text", "text": f"Voici l'hymne national du Burkina Faso, Le Ditanyé:\n\n{hymne_data[language]}"}

    # 2. Président
    if any(word in q_lower for word in ["président", "president", "chef d'état"]):
        return {"type": "text", "text": local_facts["president"]}

    # 3. Salutations
    if any(word in q_lower for word in ["bonjour", "salut", "comment ça va", "merci"]):
        if language in local_facts["salutations"]:
            saluts = local_facts["salutations"][language]
            response = f"Voici quelques salutations en {language}:\n\n"
            for key, value in saluts.items():
                if isinstance(value, list):
                    response += f"• {key.capitalize()}: {', '.join(value)}\n"
                else:
                    response += f"• {key.capitalize()}: {value}\n"
            return {"type": "text", "text": response}

    # 4. Numéros utiles
    if any(word in q_lower for word in ["numéro", "numero", "appeler", "contacter", "ussd"]):
        nums = local_facts["numeros_utiles"]
        response = "📞 Numéros utiles Orange Burkina Faso:\n\n"
        response += f"• Service client Orange: {nums['orange']['service_client']} (24/7)\n"
        response += f"• Orange Money: {nums['orange_money']['service_client']} - Menu USSD: {nums['orange_money']['menu_ussd']}\n"
        response += f"• Orange Energie: {nums['orange_energie']['service_client']} - Menu USSD: {nums['orange_energie']['menu_ussd']}\n\n"
        response += "Codes USSD utiles:\n"
        response += f"• Consulter solde: {nums['codes_ussd']['solde']}\n"
        response += f"• Recharger: {nums['codes_ussd']['recharge']}\n"
        response += f"• Transfert crédit: {nums['codes_ussd']['transfert_credit']}\n"
        return {"type": "text", "text": response}

    # SI PAS DE CONNAISSANCE LOCALE, CONTINUER AVEC RAG
    context = "\n\n".join(passages)

    # ... reste du code Groq API inchangé ...

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            model=GROQ_MODEL,
            max_tokens=200,
            temperature=0.2,
            top_p=0.95
        )

        response_text = chat_completion.choices[0].message.content.strip()
        return {"type": "text", "text": response_text}

    except Exception as e:
        print(f"Erreur Groq API: {e}")
        return {"type": "text", "text": f"Désolé, je ne peux pas répondre pour le moment. Erreur: {str(e)}"}
```

### 2.4 Adapter l'endpoint `/ask`

**Modifier l'endpoint `/ask` pour gérer les deux formats de réponse:**
```python
@app.post("/ask")
async def ask_question(request: TextQuestion):
    """
    Endpoint texte: envoie question → reçoit texte OU audio_url

    Retour JSON:
    - {"type": "text", "text": "..."}
    - {"type": "audio", "audio_url": "/audio/moore.mp3", "text": "...", "transcription": "..."}
    """
    question = request.question
    language = request.language

    try:
        # RAG: Recherche + Génération
        passages, scores = retrieve_context(question)
        response_data = generate_response(question, passages, language)

        # Ajouter les métadonnées
        result = {
            **response_data,
            "question": question,
            "language": language,
            "scores": scores.tolist()
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
```

---

## 🎨 PHASE 3: COMPOSANT REACT (Frontend)

### 3.1 Modifier `static/test_voice.html`

**Ajouter après la section de résultats:**
```html
<div id="audioPlayerContainer" style="display: none; margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 8px;">
    <h3>🎵 Lecture Audio</h3>
    <audio id="audioPlayer" controls style="width: 100%;">
        Votre navigateur ne supporte pas l'audio HTML5.
    </audio>
    <p id="audioDescription" style="margin-top: 10px; color: #666;"></p>
</div>
```

**Modifier le JavaScript pour gérer les réponses audio:**
```javascript
async function sendQuestion() {
    const question = document.getElementById('question').value;
    const resultDiv = document.getElementById('result');
    const audioPlayerContainer = document.getElementById('audioPlayerContainer');
    const audioPlayer = document.getElementById('audioPlayer');
    const audioDescription = document.getElementById('audioDescription');

    if (!question.trim()) {
        alert('Veuillez entrer une question');
        return;
    }

    resultDiv.textContent = 'Envoi de la question...';
    audioPlayerContainer.style.display = 'none';

    try {
        const response = await fetch('http://localhost:8000/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                language: 'fr'
            })
        });

        const data = await response.json();

        if (data.type === 'audio') {
            // Réponse audio
            resultDiv.textContent = data.text || 'Audio disponible ci-dessous:';
            audioPlayer.src = `http://localhost:8000${data.audio_url}`;
            audioDescription.textContent = data.description || data.transcription || '';
            audioPlayerContainer.style.display = 'block';
            audioPlayer.play();  // Lecture automatique
        } else {
            // Réponse texte
            resultDiv.textContent = data.text;
            audioPlayerContainer.style.display = 'none';
        }

    } catch (error) {
        resultDiv.textContent = `Erreur: ${error.message}`;
        audioPlayerContainer.style.display = 'none';
    }
}
```

---

## 🚀 PHASE 4: DÉPLOIEMENT & TEST

### 4.1 Redémarrer le serveur

```bash
# Arrêter l'ancien serveur
pkill -f "uvicorn.*8000"

# Démarrer le nouveau serveur
source venv/bin/activate
uvicorn data_processing.rag_server_voice:app --host 0.0.0.0 --port 8000
```

### 4.2 Tests à effectuer

**Test 1: Vérifier l'index audio**
```bash
curl http://localhost:8000/audio_index
```

**Test 2: Télécharger un fichier audio**
```bash
curl -O http://localhost:8000/audio/moore.mp3
```

**Test 3: Demander l'hymne**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Chante-moi le ditanyé", "language": "moore"}'
```

Résultat attendu:
```json
{
  "type": "audio",
  "audio_url": "/audio/moore.mp3",
  "audio_id": "moore",
  "transcription": "Hymne national du Burkina Faso en langue Moore (Ditanyé)",
  "text": "🎵 Voici l'hymne national du Burkina Faso en moore.",
  "question": "Chante-moi le ditanyé",
  "language": "moore"
}
```

**Test 4: Question normale (texte)**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment consulter mon solde?", "language": "fr"}'
```

---

## 📊 RÉSUMÉ DES FICHIERS MODIFIÉS

1. **Créés**:
   - ✅ `create_audio_index.py`
   - ✅ `audio_index.json`
   - 📄 `IMPLEMENTATION_AUDIO_SYSTEM.md` (ce document)

2. **À modifier**:
   - ⚠️ `data_processing/rag_server_voice.py` (3 modifications)
   - ⚠️ `static/test_voice.html` (ajout lecteur audio)

3. **Déjà configurés** (pas de modification):
   - ✅ `static/audio/moore.mp3`
   - ✅ `static/audio/dioula.mp3`
   - ✅ `static/audio/fulfulde.mp3`

---

## 🎯 RÉSULTAT FINAL

### Comportement du système:

| Question | Type réponse | Contenu |
|----------|--------------|---------|
| "Chante le ditanyé" | **Audio** | Fichier MP3 de l'hymne |
| "Hymne en moore" | **Audio** | moore.mp3 |
| "Qui est le président?" | **Texte** | "Ibrahim Traoré" |
| "Numéro service client?" | **Texte** | Liste numéros Orange |
| "Comment recharger?" | **Texte** | Réponse RAG + Groq |

### Avantages:
- ✅ Audio officiel pour hymnes (meilleure qualité)
- ✅ Détection automatique audio vs texte
- ✅ Fallback texte si audio non disponible
- ✅ LLM Groq stable (gardé tel quel)
- ✅ Lecteur audio intégré frontend
- ✅ API RESTful propre

---

## 📝 PROCHAINES ÉTAPES (OPTIONNELLES)

### TTS Dynamique (Phase 5)
Si vous voulez générer du TTS pour réponses sans audio:

```python
def generate_tts(text: str, output_path: str = None) -> str:
    """Génère un fichier audio avec Piper TTS"""
    if output_path is None:
        output_path = f"static/audio/generated_{hash(text) % 10000}.wav"

    # Utiliser Piper existant
    audio_data = text_to_speech_piper(text, "fr")

    with open(output_path, 'wb') as f:
        f.write(audio_data)

    return output_path
```

### Analyse Audio (Phase 6 - Avancé)
Pour extraire features prosodiques avec librosa:

```python
import librosa
import numpy as np

def analyze_audio_features(audio_path):
    """Analyse les caractéristiques audio"""
    y, sr = librosa.load(audio_path)

    # Pitch (hauteur)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    # Tempo
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

    # Intensité (RMS)
    rms = librosa.feature.rms(y=y)[0]

    return {
        "pitch_mean": float(np.mean(pitches[pitches > 0])),
        "tempo": float(tempo),
        "intensity_mean": float(np.mean(rms)),
        "duration": float(librosa.get_duration(y=y, sr=sr))
    }

# Analyser tous les hymnes
for audio_id in ["moore", "dioula", "fulfulde"]:
    features = analyze_audio_features(f"static/audio/{audio_id}.mp3")
    print(f"{audio_id}: {features}")
```

---

**🎉 FIN DU GUIDE - Système Audio Hybride Prêt!**
