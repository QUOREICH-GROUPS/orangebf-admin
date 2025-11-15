# rag_server_tts.py
# RAG Chatbot avec Synthèse Vocale (TTS)
# Optimisé pour Raspberry Pi 5

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from llama_cpp import Llama
import io
import wave
import subprocess
import tempfile

app = FastAPI(title="RAG Chatbot TTS - Orange Burkina Faso")

# ----- CONFIG -----
INDEX_FILE = "orange_faq.index"
METADATA_FILE = "metadata.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 3
MODEL_PATH = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# TTS Configuration
# Options: "piper" (meilleure qualité) ou "espeak" (plus léger, plus de langues)
TTS_ENGINE = "piper"  # ou "espeak"
PIPER_MODEL = "fr_FR-siwis-medium"  # Modèle français pour Piper
DEFAULT_LANGUAGE = "fr"  # fr, moore, dioula

# ----- CHARGEMENT DES RESSOURCES -----
print("🔄 Chargement du modèle d'embeddings...")
embed_model = SentenceTransformer(EMBEDDING_MODEL)

print("🔄 Chargement de l'index FAISS...")
if not Path(INDEX_FILE).exists() or not Path(METADATA_FILE).exists():
    raise FileNotFoundError("Index ou metadata non trouvés.")

faiss_index = faiss.read_index(INDEX_FILE)
with open(METADATA_FILE, "r") as f:
    texts = json.load(f)

print("🔄 Chargement du LLM...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    n_batch=256,
    n_gpu_layers=0,
    use_mmap=True,
    use_mlock=False,
    verbose=False
)

print("✅ Serveur prêt avec TTS!")

# ----- SCHEMAS -----
class QuestionRequest(BaseModel):
    question: str
    language: str = "fr"  # fr, moore, dioula
    enable_tts: bool = True

# ----- FONCTIONS TTS -----
def text_to_speech_piper(text: str, language: str = "fr") -> bytes:
    """
    Convertit le texte en audio avec Piper TTS
    Retourne les données audio en format WAV
    """
    # Mapping des langues vers les modèles Piper
    piper_models = {
        "fr": "fr_FR-siwis-medium",
        # Pour les langues africaines, on utilise espeak comme fallback
        "moore": None,
        "dioula": None,
    }

    model = piper_models.get(language, "fr_FR-siwis-medium")

    if model is None:
        # Fallback to espeak for unsupported languages
        return text_to_speech_espeak(text, language)

    try:
        # Créer un fichier temporaire pour l'audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        # Exécuter Piper
        # echo "text" | piper --model model_name --output_file output.wav
        process = subprocess.Popen(
            ['piper', '--model', model, '--output_file', temp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate(input=text.encode('utf-8'))

        if process.returncode != 0:
            raise Exception(f"Piper error: {stderr.decode()}")

        # Lire le fichier WAV
        with open(temp_path, 'rb') as f:
            audio_data = f.read()

        # Nettoyer le fichier temporaire
        Path(temp_path).unlink()

        return audio_data

    except FileNotFoundError:
        print("⚠️  Piper non trouvé, utilisation de espeak")
        return text_to_speech_espeak(text, language)
    except Exception as e:
        print(f"⚠️  Erreur Piper: {e}, utilisation de espeak")
        return text_to_speech_espeak(text, language)

def text_to_speech_espeak(text: str, language: str = "fr") -> bytes:
    """
    Convertit le texte en audio avec espeak-ng (fallback)
    Supporte plus de langues mais qualité moindre
    """
    # Mapping des langues vers les voix espeak
    espeak_voices = {
        "fr": "fr",
        "moore": "fr",  # Pas de support natif, on utilise fr
        "dioula": "fr",  # Pas de support natif, on utilise fr
        "fulfulde": "fr",
    }

    voice = espeak_voices.get(language, "fr")

    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        # Exécuter espeak-ng
        subprocess.run(
            ['espeak-ng', '-v', voice, '-w', temp_path, text],
            check=True,
            capture_output=True
        )

        # Lire le fichier WAV
        with open(temp_path, 'rb') as f:
            audio_data = f.read()

        # Nettoyer
        Path(temp_path).unlink()

        return audio_data

    except FileNotFoundError:
        raise Exception("espeak-ng n'est pas installé. Installez-le avec: sudo apt install espeak-ng")
    except Exception as e:
        raise Exception(f"Erreur TTS: {e}")

def get_tts_audio(text: str, language: str = "fr", engine: str = "piper") -> bytes:
    """
    Interface unifiée pour la synthèse vocale
    """
    if engine == "piper":
        return text_to_speech_piper(text, language)
    else:
        return text_to_speech_espeak(text, language)

# ----- FONCTIONS RAG -----
def retrieve_context(query: str, top_k: int = TOP_K):
    q_vec = embed_model.encode([query], convert_to_numpy=True)
    q_vec = q_vec / np.linalg.norm(q_vec, axis=1, keepdims=True)
    scores, indices = faiss_index.search(q_vec, top_k)
    passages = [texts[i] for i in indices[0]]
    return passages, scores[0]

def generate_response(question: str, passages: list):
    context = "\n\n".join(passages)

    prompt = f"""<|system|>
Tu es un assistant virtuel pour Orange Burkina Faso. Réponds aux questions en te basant UNIQUEMENT sur le contexte fourni. Si l'information n'est pas dans le contexte, dis-le poliment.<|end|>
<|user|>
Contexte:
{context}

Question: {question}<|end|>
<|assistant|>"""

    response = llm(
        prompt,
        max_tokens=200,
        temperature=0.1,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=["<|end|>", "<|user|>"],
        echo=False
    )

    return response['choices'][0]['text'].strip()

# ----- ENDPOINTS -----
@app.post("/ask")
def ask(request: QuestionRequest):
    """
    Endpoint principal: retourne la réponse textuelle et optionnellement l'audio
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    # Récupération du contexte et génération de la réponse
    passages, scores = retrieve_context(question)
    response_text = generate_response(question, passages)

    result = {
        "question": question,
        "response": response_text,
        "language": request.language,
        "retrieved_passages": passages,
        "scores": scores.tolist(),
        "audio_available": request.enable_tts
    }

    # Si TTS activé, ajouter l'URL de l'audio
    if request.enable_tts:
        result["audio_url"] = f"/tts?text={response_text}&lang={request.language}"

    return result

@app.get("/tts")
def tts_endpoint(text: str, lang: str = "fr", engine: str = None):
    """
    Endpoint TTS standalone: convertit du texte en audio
    """
    if not text:
        raise HTTPException(status_code=400, detail="Texte vide")

    # Utiliser le moteur configuré par défaut si non spécifié
    tts_engine = engine or TTS_ENGINE

    try:
        audio_data = get_tts_audio(text, lang, tts_engine)

        # Retourner l'audio en streaming
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=response_{lang}.wav"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")

@app.post("/speak")
def speak(request: QuestionRequest):
    """
    Endpoint combiné: retourne directement l'audio de la réponse
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    # Récupération et génération
    passages, scores = retrieve_context(question)
    response_text = generate_response(question, passages)

    # Générer l'audio
    try:
        audio_data = get_tts_audio(response_text, request.language, TTS_ENGINE)

        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=orange_response.wav",
                "X-Response-Text": response_text  # Texte dans le header
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "platform": "Raspberry Pi 5",
        "model": MODEL_PATH,
        "tts_engine": TTS_ENGINE,
        "tts_available": True
    }

@app.get("/voices")
def list_voices():
    """Liste les voix disponibles"""
    return {
        "piper": {
            "fr": ["fr_FR-siwis-medium", "fr_FR-siwis-low"],
            "note": "Qualité excellente, français seulement"
        },
        "espeak": {
            "fr": "Français",
            "moore": "Mooré (via français)",
            "dioula": "Dioula (via français)",
            "fulfulde": "Fulfulde (via français)",
            "note": "Qualité basique, plus de langues"
        }
    }

@app.get("/stats")
def stats():
    """Statistiques système"""
    import psutil
    mem = psutil.virtual_memory()
    return {
        "ram_total_gb": round(mem.total / 1024**3, 2),
        "ram_used_gb": round(mem.used / 1024**3, 2),
        "ram_available_gb": round(mem.available / 1024**3, 2),
        "ram_percent": mem.percent,
        "faiss_vectors": faiss_index.ntotal,
        "tts_engine": TTS_ENGINE
    }
