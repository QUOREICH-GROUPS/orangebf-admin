# rag_server_voice.py
# Assistant Vocal Complet: STT + RAG + TTS
# Optimisé pour Raspberry Pi 5

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from openai import OpenAI
import io
import subprocess
import tempfile
import os
import hashlib
import requests
import base64
from datetime import datetime, date
from threading import Lock
from collections import deque
import uuid
import zipfile
import shutil
import re
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

# Charger les variables d'environnement
load_dotenv()

app = FastAPI(title="Assistant Vocal Orange Burkina Faso - STT+RAG+TTS")

# Ajouter CORS pour l'interface web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- CONFIG -----
INDEX_FILE = "orange_faq_v2.index"
METADATA_FILE = "metadata_v2.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 3

# Configuration Groq API (cloud LLM)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# STT Configuration
STT_ENGINE = "faster-whisper"  # Options: "whisper", "vosk", "faster-whisper"
WHISPER_MODEL = "tiny"  # tiny, base, small, medium (tiny = plus rapide pour Pi)
VOSK_MODEL_PATH = "models/vosk-model-small-fr-0.22"  # Si vosk

# TTS Configuration
TTS_ENGINE = "piper"  # ou "espeak" (piper = meilleure qualité!)
PIPER_BIN = "/home/suprox/Projet/Laravel/ai/orangebf/piper_bin/piper"
PIPER_MODEL = "/home/suprox/Projet/Laravel/ai/orangebf/piper_models/fr_FR-siwis-medium.onnx"
DEFAULT_LANGUAGE = "fr"

# TTS Cache Configuration
TTS_CACHE_DIR = Path("static/tts_cache")
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
tts_cache_stats = {"hits": 0, "misses": 0}  # Pour statistiques

# Répertoires et fichiers pour la base de connaissances dynamique
KNOWLEDGE_STORE_DIR = Path("knowledge_store")
KNOWLEDGE_STORE_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_UPLOADS_DIR = KNOWLEDGE_STORE_DIR / "uploads"
KNOWLEDGE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CUSTOM_DOCS_FILE = KNOWLEDGE_STORE_DIR / "documents.json"
CUSTOM_SEGMENTS_FILE = KNOWLEDGE_STORE_DIR / "segments.json"
knowledge_documents = {}
custom_segments = []
custom_index = None
knowledge_lock = Lock()

# Paramètres en temps réel (LLM, TTS, etc.)
runtime_settings = {
    "llm_model": GROQ_MODEL,
    "tts_engine": TTS_ENGINE,
    "stt_engine": STT_ENGINE,
    "voice_profile": "piper_fr",
    "auto_play": True,
    "tts_speed": 1.0,
    "tts_pitch": 0.0
}

# Journalisation & métriques pour le tableau de bord
metrics_lock = Lock()
request_metrics = {
    "total_requests": 0,
    "requests_today": 0,
    "last_reset": date.today().isoformat(),
    "per_endpoint": {}
}
recent_logs = deque(maxlen=100)

# Paramètres réseau & robot (stockage en mémoire + refreshable)
network_settings = {
    "connection": "ethernet",
    "ethernet_ip": "",
    "wifi": {
        "ssid": "",
        "status": "disconnected",
        "ip": "",
        "signal": 0
    },
    "mqtt": {
        "enabled": False,
        "broker": "",
        "topic": "",
        "status": "offline"
    },
    "websocket_url": "",
    "microphone_enabled": True,
    "camera_enabled": True,
    "voice_recording": False,
    "system_update": {
        "auto_check": False,
        "last_check": None,
        "available": False
    }
}

# ----- CHARGEMENT DES RESSOURCES -----
print("🔄 Chargement du modèle d'embeddings...")
embed_model = SentenceTransformer(EMBEDDING_MODEL)

print("🔄 Chargement de l'index FAISS...")
if not Path(INDEX_FILE).exists() or not Path(METADATA_FILE).exists():
    raise FileNotFoundError("Index ou metadata non trouvés.")

faiss_index = faiss.read_index(INDEX_FILE)
with open(METADATA_FILE, "r") as f:
    texts = json.load(f)

print("🔄 Initialisation du client Groq API...")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY non définie dans le fichier .env")

groq_client = Groq(api_key=GROQ_API_KEY)
print(f"✅ Groq API prêt avec modèle: {GROQ_MODEL}")

# Configuration OpenAI TTS
print("🔄 Initialisation du client OpenAI TTS...")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI TTS prêt (modèle: gpt-4o-audio-preview, voice: alloy)")
else:
    openai_client = None
    print("⚠️  OPENAI_API_KEY non définie - endpoint /speak désactivé")

# Configuration Google Cloud TTS
print("🔄 Initialisation du client Google Cloud TTS...")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    print("✅ Google Cloud TTS prêt (voice: fr-FR-Wavenet-A)")
else:
    print("⚠️  GOOGLE_API_KEY non définie - endpoint /speak/google désactivé")

# Charger l'index audio
AUDIO_INDEX_FILE = "audio_index.json"
audio_map = {}  # Variable globale pour stocker l'index audio
AUDIO_STORAGE_DIR = Path("static/audio")
AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

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
            print(f"⚠️  Fichier {AUDIO_INDEX_FILE} non trouvé")
    except Exception as e:
        print(f"❌ Erreur chargement audio_index: {e}")

# Charger l'index au démarrage
print("🔄 Chargement de l'index audio...")
load_audio_index()

def save_audio_index():
    """Sauvegarde l'index audio sur disque"""
    try:
        with open(AUDIO_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(audio_map, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Erreur sauvegarde audio_index: {e}")

# Charger les salutations
SALUTATIONS_FILE = "salutations.json"
salutations_map = {}  # Variable globale pour stocker les salutations

def load_salutations():
    """Charge les salutations depuis salutations.json"""
    global salutations_map
    try:
        if Path(SALUTATIONS_FILE).exists():
            with open(SALUTATIONS_FILE, "r", encoding="utf-8") as f:
                salutations_map = json.load(f)

            # Compter les expressions par langue
            total = 0
            for langue in ["francais", "moore", "dioula", "fulfulde"]:
                if langue in salutations_map:
                    count = len(salutations_map[langue])
                    total += count
                    print(f"   - {langue.capitalize()}: {count} expressions")

            print(f"✅ Salutations chargées: {total} expressions au total")
        else:
            print(f"⚠️  Fichier {SALUTATIONS_FILE} non trouvé")
    except Exception as e:
        print(f"❌ Erreur chargement salutations: {e}")

print("🔄 Chargement des salutations...")
load_salutations()

# ----- OUTILS DE BASE -----
class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def get_data(self):
        return "".join(self.result)

def strip_html_tags(html_text: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html_text)
    return stripper.get_data()

def extract_docx_text(file_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        with zipfile.ZipFile(tmp_path) as docx_zip:
            xml_content = docx_zip.read("word/document.xml").decode("utf-8")
        root = ET.fromstring(xml_content)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            texts_nodes = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
            if texts_nodes:
                paragraphs.append("".join(texts_nodes))
        return "\n".join(paragraphs)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

def extract_pdf_text(file_bytes: bytes) -> str:
    pdftotext_bin = shutil.which("pdftotext")
    if not pdftotext_bin:
        raise HTTPException(
            status_code=415,
            detail="Conversion PDF indisponible (pdftotext absent sur le système)."
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(file_bytes)
        tmp_pdf_path = tmp_pdf.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_txt:
        tmp_txt_path = tmp_txt.name
    try:
        subprocess.run([pdftotext_bin, tmp_pdf_path, tmp_txt_path], check=True, capture_output=True)
        return Path(tmp_txt_path).read_text(encoding="utf-8", errors="ignore")
    finally:
        Path(tmp_pdf_path).unlink(missing_ok=True)
        Path(tmp_txt_path).unlink(missing_ok=True)

def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in [".txt", ".md", ".json", ".csv", ".py", ".log"]:
        return file_bytes.decode("utf-8", errors="ignore")
    if suffix in [".html", ".htm"]:
        html_text = file_bytes.decode("utf-8", errors="ignore")
        return strip_html_tags(html_text)
    if suffix == ".docx":
        return extract_docx_text(file_bytes)
    if suffix == ".pdf":
        return extract_pdf_text(file_bytes)
    raise HTTPException(
        status_code=415,
        detail=f"Format de document non supporté: {suffix or 'inconnu'}"
    )

def split_text_into_chunks(text: str, chunk_size: int = 600, overlap: int = 120) -> list:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    chunks = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if start >= length:
            break
    return chunks

def save_documents_state():
    try:
        with open(CUSTOM_DOCS_FILE, "w", encoding="utf-8") as f:
            json.dump(knowledge_documents, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Erreur sauvegarde documents: {e}")

    try:
        with open(CUSTOM_SEGMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_segments, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Erreur sauvegarde segments: {e}")

def rebuild_custom_index():
    """Reconstruit l'index FAISS des documents importés via l'UI"""
    global custom_index
    if not custom_segments:
        custom_index = None
        return

    texts_segments = [segment["text"] for segment in custom_segments]
    embeddings = embed_model.encode(texts_segments, convert_to_numpy=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    custom_index = faiss.IndexFlatIP(embeddings.shape[1])
    custom_index.add(embeddings)
    print(f"✅ Index personnalisé reconstruit ({custom_index.ntotal} segments)")

def load_custom_documents():
    global knowledge_documents, custom_segments
    if CUSTOM_DOCS_FILE.exists():
        try:
            knowledge_documents = json.loads(CUSTOM_DOCS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Impossible de charger {CUSTOM_DOCS_FILE}: {e}")
            knowledge_documents = {}
    if CUSTOM_SEGMENTS_FILE.exists():
        try:
            custom_segments = json.loads(CUSTOM_SEGMENTS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Impossible de charger {CUSTOM_SEGMENTS_FILE}: {e}")
            custom_segments = []
    rebuild_custom_index()

def add_log(message: str, scope: str = "system", level: str = "info"):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": message,
        "scope": scope,
        "level": level
    }
    recent_logs.appendleft(entry)

def _reset_metrics_if_needed():
    today = date.today().isoformat()
    if request_metrics["last_reset"] != today:
        request_metrics["last_reset"] = today
        request_metrics["requests_today"] = 0

def record_request(endpoint: str):
    with metrics_lock:
        _reset_metrics_if_needed()
        request_metrics["total_requests"] += 1
        request_metrics["requests_today"] += 1
        request_metrics["per_endpoint"][endpoint] = request_metrics["per_endpoint"].get(endpoint, 0) + 1

def get_metrics_snapshot():
    with metrics_lock:
        return {
            "total_requests": request_metrics["total_requests"],
            "requests_today": request_metrics["requests_today"],
            "last_reset": request_metrics["last_reset"],
            "per_endpoint": request_metrics["per_endpoint"],
            "logs": list(recent_logs)
        }

# Charger les documents personnalisés existants au démarrage
print("🔄 Chargement des documents personnalisés...")
load_custom_documents()

def format_response_text(text: str) -> str:
    """Nettoie les réponses pour supprimer le markdown et les bullets bruts"""
    if not text:
        return ""
    clean = text.replace("**", " ").replace("__", " ")
    clean = re.sub(r"\*(?!\d)([^*]+)\*", r"\1", clean)
    clean = re.sub(r"(?m)^\s*-\s+", "• ", clean)
    clean = re.sub(r"\s+\n", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    clean = re.sub(r"[ \t]{2,}", " ", clean)
    return clean.strip()

def _remove_segments_for_document(doc_id: str):
    global custom_segments
    if not custom_segments:
        return
    custom_segments = [segment for segment in custom_segments if segment.get("doc_id") != doc_id]

def _persist_document(
    doc_id: str,
    stored_filename: str,
    original_name: str,
    category: str,
    chunks: list[str],
    size_bytes: int
):
    """Sauvegarde les métadonnées + segments pour un document importé"""
    global knowledge_documents
    now = datetime.utcnow().isoformat() + "Z"
    metadata = {
        "id": doc_id,
        "original_name": original_name,
        "filename": stored_filename,
        "path": str(KNOWLEDGE_UPLOADS_DIR / stored_filename),
        "category": category,
        "segments": len(chunks),
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "created_at": knowledge_documents.get(doc_id, {}).get("created_at", now),
        "last_indexed_at": now,
        "segment_preview": chunks[0][:200] + ("..." if len(chunks[0]) > 200 else "") if chunks else ""
    }

    knowledge_documents[doc_id] = metadata
    _remove_segments_for_document(doc_id)

    for order, chunk in enumerate(chunks):
        custom_segments.append({
            "doc_id": doc_id,
            "text": chunk,
            "order": order
        })

    save_documents_state()
    rebuild_custom_index()
    return metadata

def convert_audio_to_wav(source_path: Path, target_path: Path):
    """Convertit un fichier audio (mp3/wav/etc.) en wav via ffmpeg"""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise HTTPException(status_code=500, detail="ffmpeg n'est pas installé sur le système")
    subprocess.run(
        [ffmpeg_bin, "-y", "-i", str(source_path), str(target_path)],
        check=True,
        capture_output=True
    )

# Initialisation STT (lazy loading)
whisper_model = None
vosk_model = None

print("✅ Serveur vocal prêt!")

# ----- SCHEMAS -----
class VoiceRequest(BaseModel):
    language: str = "fr"
    response_format: str = "both"  # "text", "audio", "both"

class TextQuestion(BaseModel):
    question: str
    language: str = "fr"
    enable_voice: bool = True

class SpeakRequest(BaseModel):
    text: str

class DialogueSettingsUpdate(BaseModel):
    llm_model: str | None = None
    tts_engine: str | None = None
    stt_engine: str | None = None
    voice_profile: str | None = None
    auto_play: bool | None = None
    tts_speed: float | None = None
    tts_pitch: float | None = None

class NetworkSettingsUpdate(BaseModel):
    connection: str | None = None
    ethernet_ip: str | None = None
    wifi: dict | None = None
    mqtt: dict | None = None
    websocket_url: str | None = None
    microphone_enabled: bool | None = None
    camera_enabled: bool | None = None
    voice_recording: bool | None = None
    system_update: dict | None = None

# ----- FONCTIONS STT -----
def init_whisper():
    """Initialisation lazy de Whisper"""
    global whisper_model
    if whisper_model is None:
        try:
            import whisper
            print(f"🔄 Chargement de Whisper ({WHISPER_MODEL})...")
            whisper_model = whisper.load_model(WHISPER_MODEL)
            print("✅ Whisper chargé")
        except ImportError:
            raise Exception("Whisper non installé. Installez: pip install openai-whisper")
    return whisper_model

def init_vosk():
    """Initialisation lazy de Vosk"""
    global vosk_model
    if vosk_model is None:
        try:
            from vosk import Model
            print(f"🔄 Chargement de Vosk...")
            if not Path(VOSK_MODEL_PATH).exists():
                raise FileNotFoundError(f"Modèle Vosk non trouvé: {VOSK_MODEL_PATH}")
            vosk_model = Model(VOSK_MODEL_PATH)
            print("✅ Vosk chargé")
        except ImportError:
            raise Exception("Vosk non installé. Installez: pip install vosk")
    return vosk_model

def speech_to_text_whisper(audio_file: str, language: str = "fr") -> str:
    """
    Transcription audio avec Whisper
    Retourne le texte transcrit
    """
    model = init_whisper()

    # Mapping des codes de langue
    lang_map = {
        "fr": "french",
        "moore": "french",  # Pas de support natif, on utilise français
        "dioula": "french",
        "fulfulde": "french"
    }

    whisper_lang = lang_map.get(language, "french")

    try:
        result = model.transcribe(
            audio_file,
            language=whisper_lang if whisper_lang != "french" else "fr",
            fp16=False  # Désactiver FP16 pour CPU
        )
        return result["text"].strip()
    except Exception as e:
        raise Exception(f"Erreur Whisper: {e}")

def speech_to_text_vosk(audio_file: str, language: str = "fr") -> str:
    """
    Transcription audio avec Vosk
    """
    model = init_vosk()

    try:
        from vosk import KaldiRecognizer
        import wave

        # Ouvrir le fichier WAV
        wf = wave.open(audio_file, "rb")

        # Créer le recognizer
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        # Transcrire
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if "text" in result:
                    results.append(result["text"])

        # Résultat final
        final = json.loads(rec.FinalResult())
        if "text" in final:
            results.append(final["text"])

        return " ".join(results).strip()

    except Exception as e:
        raise Exception(f"Erreur Vosk: {e}")

def speech_to_text_faster_whisper(audio_file: str, language: str = "fr") -> str:
    """
    Transcription avec Faster-Whisper (plus rapide que Whisper standard)
    """
    try:
        from faster_whisper import WhisperModel

        # Charger le modèle (cache automatique)
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

        segments, info = model.transcribe(audio_file, language=language, beam_size=5)

        text = " ".join([segment.text for segment in segments])
        return text.strip()

    except ImportError:
        raise Exception("Faster-Whisper non installé. Installez: pip install faster-whisper")
    except Exception as e:
        raise Exception(f"Erreur Faster-Whisper: {e}")

def transcribe_audio(audio_file: str, language: str = "fr", engine: str = None) -> str:
    """
    Interface unifiée pour la transcription audio
    """
    stt = engine or STT_ENGINE

    if stt == "whisper":
        return speech_to_text_whisper(audio_file, language)
    elif stt == "vosk":
        return speech_to_text_vosk(audio_file, language)
    elif stt == "faster-whisper":
        return speech_to_text_faster_whisper(audio_file, language)
    else:
        raise Exception(f"Moteur STT inconnu: {stt}")

# ----- FONCTIONS TTS -----
def text_to_speech_piper(text: str, language: str = "fr") -> bytes:
    """Convertit texte en audio avec Piper + Cache"""
    # Pour l'instant, seulement français est supporté avec Piper
    if language != "fr":
        return text_to_speech_espeak(text, language)

    # Calculer le hash du texte pour le cache
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    cache_file = TTS_CACHE_DIR / f"{text_hash}_{language}.wav"

    # Vérifier si dans le cache
    if cache_file.exists():
        tts_cache_stats["hits"] += 1
        print(f"✅ TTS Cache HIT: {text[:50]}... (hash: {text_hash[:8]}...)")
        with open(cache_file, 'rb') as f:
            return f.read()

    # Cache miss - générer le TTS
    tts_cache_stats["misses"] += 1
    print(f"⚙️  TTS Cache MISS: {text[:50]}... (génération en cours)")

    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        # Utiliser les chemins absolus définis en configuration
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '/home/suprox/Projet/Laravel/ai/orangebf/piper_bin'

        process = subprocess.Popen(
            [PIPER_BIN, '--model', PIPER_MODEL, '--output_file', temp_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        stdout, stderr = process.communicate(input=text.encode('utf-8'))

        if process.returncode != 0:
            print(f"Erreur Piper: {stderr.decode()}")
            return text_to_speech_espeak(text, language)

        with open(temp_path, 'rb') as f:
            audio_data = f.read()

        # Sauvegarder dans le cache
        try:
            with open(cache_file, 'wb') as f:
                f.write(audio_data)
            print(f"💾 TTS sauvegardé dans cache: {cache_file.name}")
        except Exception as cache_error:
            print(f"⚠️  Erreur sauvegarde cache: {cache_error}")

        Path(temp_path).unlink()
        return audio_data

    except Exception as e:
        print(f"Exception Piper: {e}")
        return text_to_speech_espeak(text, language)

def text_to_speech_espeak(text: str, language: str = "fr") -> bytes:
    """Convertit texte en audio avec espeak-ng"""
    espeak_voices = {
        "fr": "fr",
        "moore": "fr",
        "dioula": "fr",
        "fulfulde": "fr",
    }

    voice = espeak_voices.get(language, "fr")

    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        subprocess.run(
            ['espeak-ng', '-v', voice, '-w', temp_path, text],
            check=True,
            capture_output=True
        )

        with open(temp_path, 'rb') as f:
            audio_data = f.read()

        Path(temp_path).unlink()
        return audio_data

    except Exception as e:
        raise Exception(f"Erreur TTS: {e}")

def get_tts_audio(text: str, language: str = "fr", engine: str | None = None) -> bytes:
    """Interface unifiée TTS"""
    target_engine = engine or runtime_settings.get("tts_engine", TTS_ENGINE)
    if target_engine == "piper":
        return text_to_speech_piper(text, language)
    return text_to_speech_espeak(text, language)

# ----- FONCTIONS RAG -----
# Importer les connaissances locales
import sys
sys.path.insert(0, str(Path(__file__).parent))
from local_knowledge import get_fact, local_facts

def retrieve_context(query: str, top_k: int = TOP_K):
    q_vec = embed_model.encode([query], convert_to_numpy=True)
    q_vec = q_vec / np.linalg.norm(q_vec, axis=1, keepdims=True)

    combined = []

    if faiss_index is not None and faiss_index.ntotal > 0:
        limit = min(top_k, faiss_index.ntotal)
        base_scores, base_indices = faiss_index.search(q_vec, limit)
        for idx, score in zip(base_indices[0], base_scores[0]):
            combined.append({
                "text": texts[idx],
                "score": float(score),
                "source": "base"
            })

    if custom_index is not None and custom_index.ntotal > 0 and custom_segments:
        limit = min(top_k, custom_index.ntotal)
        custom_scores, custom_indices = custom_index.search(q_vec, limit)
        for idx, score in zip(custom_indices[0], custom_scores[0]):
            segment = custom_segments[idx]
            combined.append({
                "text": segment["text"],
                "score": float(score),
                "source": "custom",
                "doc_id": segment.get("doc_id")
            })

    if not combined:
        return [], np.array([])

    combined.sort(key=lambda item: item["score"], reverse=True)
    selected = combined[:top_k]
    passages = [item["text"] for item in selected]
    scores = np.array([item["score"] for item in selected], dtype=np.float32)
    return passages, scores

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
                "text": format_response_text(f"🎵 Voici l'hymne national du Burkina Faso en {audio_info['langue']}.")
            }
        else:
            # Fallback texte si audio non disponible
            hymne_data = local_facts["hymne"]
            if language in hymne_data:
                return {"type": "text", "text": format_response_text(f"Voici l'hymne national du Burkina Faso, Le Ditanyé:\n\n{hymne_data[language]}")}
            else:
                return {"type": "text", "text": format_response_text(f"Voici l'hymne national du Burkina Faso, Le Ditanyé:\n\n{hymne_data['francais']}")}

    # 2. Président
    if any(word in q_lower for word in ["président", "president", "chef d'état", "chef de l'état"]):
        return {"type": "text", "text": format_response_text(local_facts["president"])}

    # 3. Salutations
    if any(word in q_lower for word in ["bonjour", "salut", "comment ça va", "bonsoir", "merci", "au revoir"]):
        if language in local_facts["salutations"]:
            saluts = local_facts["salutations"][language]
            response = f"Voici quelques salutations en {language}:\n\n"
            for key, value in saluts.items():
                if isinstance(value, list):
                    response += f"• {key.capitalize()}: {', '.join(value)}\n"
                else:
                    response += f"• {key.capitalize()}: {value}\n"
            return {"type": "text", "text": format_response_text(response)}

    # 4. Numéros utiles Orange
    if any(word in q_lower for word in ["numéro", "numero", "appeler", "contacter", "téléphone", "telephone", "ussd", "code"]):
        nums = local_facts["numeros_utiles"]
        response = "📞 Numéros utiles Orange Burkina Faso:\n\n"
        response += f"• Service client Orange: {nums['orange']['service_client']} (24/7)\n"
        response += f"• Orange Money: {nums['orange_money']['service_client']} - Menu USSD: {nums['orange_money']['menu_ussd']}\n"
        response += f"• Orange Energie: {nums['orange_energie']['service_client']} - Menu USSD: {nums['orange_energie']['menu_ussd']}\n\n"
        response += "Codes USSD utiles:\n"
        response += f"• Consulter solde: {nums['codes_ussd']['solde']}\n"
        response += f"• Recharger: {nums['codes_ussd']['recharge']}\n"
        response += f"• Transfert crédit: {nums['codes_ussd']['transfert_credit']}\n"
        response += f"• Connaître votre numéro: {nums['codes_ussd']['numero_orange']}\n"
        return {"type": "text", "text": format_response_text(response)}

    # SI PAS DE CONNAISSANCE LOCALE, CONTINUER AVEC RAG
    context = "\n\n".join(passages)

    # Messages système et utilisateur selon la langue
    if language == "fr":
        system_msg = "Tu es un assistant Orange Burkina Faso. Tu parles UNIQUEMENT en français. NE JAMAIS répondre en anglais, toujours en français clair et précis."
        user_msg = f"""Voici des informations sur Orange Burkina Faso:
{context}

Question du client: {question}

Réponds en français de manière claire, concise et professionnelle."""

    elif language == "en":
        system_msg = "You are an Orange Burkina Faso assistant. You speak ONLY in English. NEVER answer in French, always in clear and precise English."
        user_msg = f"""Here is information about Orange Burkina Faso:
{context}

Customer question: {question}

Answer in English clearly, concisely and professionally."""

    else:
        # Mooré, Dioula, Fulfulde -> fallback français
        system_msg = f"Tu es un assistant Orange Burkina Faso. Réponds en {language} si possible, sinon en français."
        user_msg = f"""Contexte:
{context}

Question: {question}"""

    try:
        # Appel à l'API Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            model=runtime_settings.get("llm_model", GROQ_MODEL),
            max_tokens=200,
            temperature=0.2,
            top_p=0.95
        )

        response_text = chat_completion.choices[0].message.content.strip()
        response_text = format_response_text(response_text)
        return {"type": "text", "text": response_text}

    except Exception as e:
        print(f"Erreur Groq API: {e}")
        return {"type": "text", "text": f"Désolé, je ne peux pas répondre pour le moment. Erreur: {str(e)}"}

# ----- ENDPOINTS -----

@app.post("/voice/ask")
async def voice_ask(
    audio: UploadFile = File(...),
    language: str = "fr",
    response_format: str = "both"
):
    """
    Endpoint principal: envoie audio → reçoit texte et/ou audio

    Usage:
    curl -X POST http://localhost:8000/voice/ask \
      -F "audio=@question.wav" \
      -F "language=fr" \
      -F "response_format=both"
    """

    try:
        # Sauvegarder l'audio uploadé
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name

        record_request("voice/ask")

        # 1. STT: Audio → Texte
        print("🎤 Transcription...")
        stt_engine = runtime_settings.get("stt_engine", STT_ENGINE)
        question = transcribe_audio(temp_path, language, stt_engine)
        print(f"📝 Question détectée: {question}")

        # 2. RAG: Recherche + Génération
        print("🔍 Recherche...")
        passages, scores = retrieve_context(question)
        print("🤖 Génération de la réponse...")
        response_data = generate_response(question, passages, language)

        # Extraire le texte de la réponse (peut être dict avec type="text" ou type="audio")
        if isinstance(response_data, dict):
            response_text = response_data.get("text", "")
        else:
            response_text = str(response_data)

        print(f"✅ Réponse: {response_text[:100] if response_text else 'Audio response'}...")

        # 3. TTS: Texte → Audio (si demandé)
        audio_data = None
        if response_format in ["audio", "both"]:
            print("🔊 Synthèse vocale...")
            tts_engine = runtime_settings.get("tts_engine", TTS_ENGINE)
            audio_data = get_tts_audio(response_text, language, tts_engine)

        # Nettoyer le fichier temporaire
        Path(temp_path).unlink()

        # Retourner selon le format demandé
        if response_format == "text":
            result = {
                "question": question,
                "response": response_text,
                "language": language,
                "scores": scores.tolist()
            }
        elif response_format == "audio":
            add_log(f"Interaction vocale (stream) traitée ({language})", scope="voice")
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/wav",
                headers={
                    "X-Question": question,
                    "X-Response-Text": response_text
                }
            )
        else:  # both
            # Encoder l'audio en base64 pour JSON
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')

            result = {
                "question": question,
                "response": response_text,
                "language": language,
                "scores": scores.tolist(),
                "audio_base64": audio_b64,
                "audio_download_url": f"/tts?text={response_text}&lang={language}"
            }

        add_log(f"Interaction vocale traitée ({language})", scope="voice")
        return result

    except Exception as e:
        # Nettoyer en cas d'erreur
        if 'temp_path' in locals() and Path(temp_path).exists():
            Path(temp_path).unlink()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/voice/transcribe")
async def transcribe_only(audio: UploadFile = File(...), language: str = "fr"):
    """
    Endpoint STT standalone: audio → texte
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name

        stt_engine = runtime_settings.get("stt_engine", STT_ENGINE)
        record_request("voice/transcribe")
        text = transcribe_audio(temp_path, language, stt_engine)
        Path(temp_path).unlink()
        add_log(f"Transcription audio réussie ({language})", scope="stt")

        return {
            "text": text,
            "language": language,
            "engine": stt_engine
        }
    except Exception as e:
        if 'temp_path' in locals() and Path(temp_path).exists():
            Path(temp_path).unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text/ask")
def text_ask(request: TextQuestion):
    """
    Endpoint texte: envoie question → reçoit texte OU audio_url

    Retour JSON:
    - {"type": "text", "text": "...", ...}
    - {"type": "audio", "audio_url": "/audio/moore.mp3", "text": "...", "transcription": "...", ...}
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    record_request("text/ask")
    passages, scores = retrieve_context(question)
    response_data = generate_response(question, passages, request.language)

    # Ajouter les métadonnées
    if response_data.get("type") == "text" and response_data.get("text"):
        response_data["text"] = format_response_text(response_data["text"])

    result = {
        **response_data,
        "question": question,
        "language": request.language,
        "scores": scores.tolist()
    }

    # Pour les réponses texte avec enable_voice activé, ajouter TTS
    if request.enable_voice and response_data.get("type") == "text":
        result["tts_url"] = f"/tts?text={response_data['text']}&lang={request.language}"

    add_log(f"Question texte traitée ({request.language})", scope="text")
    return result

@app.get("/tts")
def tts_endpoint(text: str, lang: str = "fr"):
    """Convertit du texte en audio"""
    if not text:
        raise HTTPException(status_code=400, detail="Texte vide")

    try:
        record_request("tts")
        audio_data = get_tts_audio(text, lang, runtime_settings.get("tts_engine", TTS_ENGINE))
        add_log(f"TTS généré ({lang})", scope="tts")
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename=tts_{lang}.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----- GESTION BASE DE CONNAISSANCES -----
@app.get("/knowledge/documents")
def list_documents():
    """Retourne la liste des documents importés via l'UI"""
    sorted_docs = sorted(knowledge_documents.values(), key=lambda d: d.get("last_indexed_at", ""), reverse=True)
    return {
        "count": len(sorted_docs),
        "documents": sorted_docs,
        "segments_indexed": custom_index.ntotal if custom_index else 0
    }

@app.get("/knowledge/segments/{doc_id}")
def list_segments(doc_id: str):
    if doc_id not in knowledge_documents:
        raise HTTPException(status_code=404, detail="Document introuvable")
    segments = sorted(
        (segment for segment in custom_segments if segment.get("doc_id") == doc_id),
        key=lambda seg: seg.get("order", 0)
    )
    return {
        "count": len(segments),
        "segments": segments
    }

@app.post("/knowledge/documents")
async def upload_document(category: str = Form("general"), file: UploadFile = File(...)):
    """Import (upload) d'un document dans la base RAG"""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Fichier vide")

    original_name = file.filename or "document.txt"
    text = extract_text_from_file(original_name, file_bytes)
    chunks = split_text_into_chunks(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Impossible d'extraire du texte du document")

    doc_id = uuid.uuid4().hex[:12]
    suffix = Path(original_name).suffix.lower() or ".txt"
    stored_filename = f"{doc_id}{suffix}"
    stored_path = KNOWLEDGE_UPLOADS_DIR / stored_filename
    stored_path.write_bytes(file_bytes)

    with knowledge_lock:
        metadata = _persist_document(
            doc_id,
            stored_filename,
            original_name,
            category,
            chunks,
            len(file_bytes)
        )

    record_request("knowledge/upload")
    add_log(f"Document '{original_name}' importé ({len(chunks)} segments)", scope="knowledge")
    return {"status": "indexed", "document": metadata}

@app.post("/knowledge/documents/{doc_id}/reindex")
def reindex_document(doc_id: str):
    """Reprocess un document déjà importé"""
    if doc_id not in knowledge_documents:
        raise HTTPException(status_code=404, detail="Document introuvable")

    doc_meta = knowledge_documents[doc_id]
    stored_path = Path(doc_meta["path"])
    if not stored_path.exists():
        raise HTTPException(status_code=404, detail="Fichier original introuvable sur le disque")

    file_bytes = stored_path.read_bytes()
    text = extract_text_from_file(doc_meta["original_name"], file_bytes)
    chunks = split_text_into_chunks(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Impossible de reindexer: texte vide")

    with knowledge_lock:
        metadata = _persist_document(
            doc_id,
            doc_meta["filename"],
            doc_meta["original_name"],
            doc_meta.get("category", "general"),
            chunks,
            len(file_bytes)
        )

    record_request("knowledge/reindex")
    add_log(f"Document '{doc_meta['original_name']}' réindexé ({len(chunks)} segments)", scope="knowledge")
    return {"status": "reindexed", "document": metadata}

@app.delete("/knowledge/documents/{doc_id}")
def delete_document(doc_id: str):
    if doc_id not in knowledge_documents:
        raise HTTPException(status_code=404, detail="Document introuvable")

    doc_meta = knowledge_documents.pop(doc_id)
    _remove_segments_for_document(doc_id)
    save_documents_state()
    rebuild_custom_index()

    stored_path = Path(doc_meta["path"])
    if stored_path.exists():
        stored_path.unlink()

    record_request("knowledge/delete")
    add_log(f"Document '{doc_meta['original_name']}' supprimé", scope="knowledge", level="warning")
    return {"status": "deleted", "document": doc_meta}

@app.post("/audio/upload")
async def upload_audio(
    category: str = Form("hymne_national"),
    langue: str = Form("fr"),
    description: str = Form(""),
    convert_wav: bool = Form(False),
    file: UploadFile = File(...)
):
    """Ajoute un fichier audio (hymne, salutations, phrases)"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Fichier audio vide")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in [".mp3", ".wav", ".ogg", ".m4a", ".webm"]:
        raise HTTPException(status_code=415, detail=f"Extension audio non supportée: {extension}")

    audio_id = uuid.uuid4().hex[:10]
    stored_filename = f"{audio_id}{extension}"
    stored_path = AUDIO_STORAGE_DIR / stored_filename
    stored_path.write_bytes(data)

    entry = {
        "id": audio_id,
        "filename": stored_filename,
        "path": str(stored_path),
        "size_bytes": len(data),
        "size_mb": round(len(data) / (1024 * 1024), 2),
        "langue": langue,
        "categorie": category,
        "description": description or f"Audio importé ({category})",
        "uploaded_at": datetime.utcnow().isoformat() + "Z"
    }

    # Conversion facultative en WAV
    if convert_wav and extension != ".wav":
        wav_filename = f"{audio_id}.wav"
        wav_path = AUDIO_STORAGE_DIR / wav_filename
        convert_audio_to_wav(stored_path, wav_path)
        entry["alternate_wav"] = wav_filename

    audio_map[audio_id] = entry
    save_audio_index()

    record_request("audio/upload")
    add_log(f"Audio '{file.filename}' ajouté ({category})", scope="audio")
    return {"status": "stored", "audio": entry}

@app.post("/audio/{audio_id}/replace")
async def replace_audio(
    audio_id: str,
    langue: str = Form(None),
    categorie: str = Form(None),
    description: str = Form(None),
    file: UploadFile = File(None)
):
    """Remplace les métadonnées ou le contenu d'un audio existant"""
    if audio_id not in audio_map:
        raise HTTPException(status_code=404, detail="Audio introuvable")

    entry = audio_map[audio_id]

    if file is not None:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Nouveau fichier audio vide")
        extension = Path(file.filename or "").suffix.lower()
        new_filename = f"{audio_id}{extension}"
        new_path = AUDIO_STORAGE_DIR / new_filename
        new_path.write_bytes(data)

        # Supprimer l'ancien fichier si différent
        old_path = Path(entry["path"])
        if old_path.exists() and old_path != new_path:
            old_path.unlink()

        entry["filename"] = new_filename
        entry["path"] = str(new_path)
        entry["size_bytes"] = len(data)
        entry["size_mb"] = round(len(data) / (1024 * 1024), 2)

    if langue is not None:
        entry["langue"] = langue
    if categorie is not None:
        entry["categorie"] = categorie
    if description is not None:
        entry["description"] = description

    audio_map[audio_id] = entry
    save_audio_index()

    record_request("audio/update")
    add_log(f"Audio '{audio_id}' mis à jour", scope="audio")
    return {"status": "updated", "audio": entry}

@app.post("/audio/{audio_id}/convert")
def convert_audio_endpoint(audio_id: str):
    """Convertit un audio existant en WAV (pour tests Raspberry)"""
    if audio_id not in audio_map:
        raise HTTPException(status_code=404, detail="Audio introuvable")

    entry = audio_map[audio_id]
    source_path = Path(entry["path"])
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Fichier source introuvable")

    wav_filename = f"{audio_id}.wav"
    wav_path = AUDIO_STORAGE_DIR / wav_filename
    convert_audio_to_wav(source_path, wav_path)

    entry["alternate_wav"] = wav_filename
    audio_map[audio_id] = entry
    save_audio_index()

    record_request("audio/convert")
    add_log(f"Audio '{audio_id}' converti en WAV", scope="audio")
    return {"status": "converted", "audio": entry}

@app.delete("/audio/{audio_id}")
def delete_audio(audio_id: str):
    if audio_id not in audio_map:
        raise HTTPException(status_code=404, detail="Audio introuvable")

    entry = audio_map.pop(audio_id)
    save_audio_index()

    for key in ["path", "alternate_wav"]:
        file_value = entry.get(key)
        if not file_value:
            continue
        file_path = Path(file_value if key == "path" else AUDIO_STORAGE_DIR / file_value)
        if file_path.exists():
            file_path.unlink()

    record_request("audio/delete")
    add_log(f"Audio '{audio_id}' supprimé", scope="audio", level="warning")
    return {"status": "deleted", "audio": entry}

@app.get("/admin/metrics")
def admin_metrics():
    """Expose les métriques + journaux pour le tableau de bord"""
    snapshot = get_metrics_snapshot()
    knowledge_segments = custom_index.ntotal if custom_index else 0
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
    except Exception:
        cpu = None

    return {
        "requests": snapshot,
        "tts_cache": tts_cache_stats,
        "audio_files": len(audio_map),
        "knowledge_segments": knowledge_segments,
        "cpu_percent": cpu
    }

@app.post("/admin/restart")
def restart_robot():
    """Simule un redémarrage logiciel du robot"""
    record_request("admin/restart")
    add_log("Redémarrage demandé depuis l'interface admin", scope="system", level="warning")
    return {
        "status": "scheduled",
        "message": "Redémarrage simulé. Exécutez la commande système appropriée sur le Raspberry Pi."
    }

@app.get("/settings/dialogue")
def get_dialogue_settings():
    """Retourne les paramètres LLM + TTS utilisés par l'assistant"""
    return {
        "settings": runtime_settings,
        "options": {
            "llm_models": [
                "llama-3.1-8b-instant",
                "llama-3.1-70b-versatile",
                "mixtral-8x7b",
                runtime_settings.get("llm_model")
            ],
            "tts_engines": ["piper", "espeak"],
            "stt_engines": ["faster-whisper", "whisper", "vosk"],
            "voice_profiles": ["piper_fr", "edge_henri", runtime_settings.get("voice_profile", "piper_fr")]
        }
    }

@app.post("/settings/dialogue")
def update_dialogue_settings(payload: DialogueSettingsUpdate):
    """Met à jour les paramètres LLM/TTS/STT"""
    allowed_tts = {"piper", "espeak"}
    allowed_stt = {"faster-whisper", "whisper", "vosk"}
    changed = {}

    if payload.llm_model:
        runtime_settings["llm_model"] = payload.llm_model
        changed["llm_model"] = payload.llm_model

    if payload.tts_engine:
        if payload.tts_engine not in allowed_tts:
            raise HTTPException(status_code=400, detail=f"Moteur TTS invalide: {payload.tts_engine}")
        runtime_settings["tts_engine"] = payload.tts_engine
        changed["tts_engine"] = payload.tts_engine

    if payload.stt_engine:
        if payload.stt_engine not in allowed_stt:
            raise HTTPException(status_code=400, detail=f"Moteur STT invalide: {payload.stt_engine}")
        runtime_settings["stt_engine"] = payload.stt_engine
        changed["stt_engine"] = payload.stt_engine

    if payload.voice_profile is not None:
        runtime_settings["voice_profile"] = payload.voice_profile
        changed["voice_profile"] = payload.voice_profile

    if payload.auto_play is not None:
        runtime_settings["auto_play"] = payload.auto_play
        changed["auto_play"] = payload.auto_play

    if payload.tts_speed is not None:
        runtime_settings["tts_speed"] = payload.tts_speed
        changed["tts_speed"] = payload.tts_speed

    if payload.tts_pitch is not None:
        runtime_settings["tts_pitch"] = payload.tts_pitch
        changed["tts_pitch"] = payload.tts_pitch

    if not changed:
        return {"status": "no_change", "settings": runtime_settings}

    record_request("settings/dialogue")
    add_log(f"Paramètres dialogue mis à jour: {', '.join(changed.keys())}", scope="settings")
    return {"status": "updated", "changed": changed, "settings": runtime_settings}

@app.get("/settings/network")
def get_network_settings():
    """Retourne l'état du réseau et des capteurs"""
    return {"settings": network_settings}

@app.post("/settings/network")
def update_network_settings(update: NetworkSettingsUpdate):
    """Met à jour la configuration réseau/capteurs"""
    changed = {}
    if update.connection:
        network_settings["connection"] = update.connection
        changed["connection"] = update.connection
    if update.ethernet_ip is not None:
        network_settings["ethernet_ip"] = update.ethernet_ip
        changed["ethernet_ip"] = update.ethernet_ip
    if update.wifi:
        network_settings["wifi"].update(update.wifi)
        changed["wifi"] = network_settings["wifi"]
    if update.mqtt:
        network_settings["mqtt"].update(update.mqtt)
        changed["mqtt"] = network_settings["mqtt"]
    if update.websocket_url is not None:
        network_settings["websocket_url"] = update.websocket_url
        changed["websocket_url"] = update.websocket_url
    if update.microphone_enabled is not None:
        network_settings["microphone_enabled"] = update.microphone_enabled
        changed["microphone_enabled"] = update.microphone_enabled
    if update.camera_enabled is not None:
        network_settings["camera_enabled"] = update.camera_enabled
        changed["camera_enabled"] = update.camera_enabled
    if update.voice_recording is not None:
        network_settings["voice_recording"] = update.voice_recording
        changed["voice_recording"] = update.voice_recording
    if update.system_update:
        network_settings["system_update"].update(update.system_update)
        changed["system_update"] = network_settings["system_update"]

    if not changed:
        return {"status": "no_change", "settings": network_settings}

    record_request("settings/network")
    add_log(f"Paramètres réseau mis à jour: {', '.join(changed.keys())}", scope="network")
    return {"status": "updated", "settings": network_settings, "changed": changed}

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

@app.get("/salutations")
async def get_salutations():
    """
    Retourne toutes les salutations
    Usage: GET /salutations
    """
    # Compter total d'expressions
    total = sum(len(salutations_map.get(langue, {})) for langue in ["francais", "moore", "dioula", "fulfulde"])

    return {
        "count": total,
        "langues": ["francais", "moore", "dioula", "fulfulde"],
        "data": salutations_map
    }

@app.get("/salutations/{langue}")
async def get_salutations_by_language(langue: str):
    """
    Retourne les salutations d'une langue spécifique
    Usage: GET /salutations/francais
    """
    if langue not in salutations_map:
        raise HTTPException(
            status_code=404,
            detail=f"Langue '{langue}' non trouvée. Langues disponibles: francais, moore, dioula, fulfulde"
        )

    return {
        "langue": langue,
        "count": len(salutations_map[langue]),
        "salutations": salutations_map[langue]
    }

@app.post("/load_salutations")
async def reload_salutations():
    """
    Recharge les salutations depuis salutations.json
    Usage: POST /load_salutations
    """
    load_salutations()
    total = sum(len(salutations_map.get(langue, {})) for langue in ["francais", "moore", "dioula", "fulfulde"])

    return {
        "status": "success",
        "message": f"Salutations rechargées: {total} expressions",
        "langues": list(salutations_map.keys())
    }

@app.post("/speak")
async def speak(request: SpeakRequest):
    """
    Génère de l'audio depuis du texte en utilisant OpenAI TTS

    Usage: POST /speak avec JSON {"text": "votre texte"}
    Retourne: Fichier audio MP3

    Exemple:
        curl -X POST -H "Content-Type: application/json" \\
             -d '{"text":"Bonjour et bienvenue!"}' \\
             http://localhost:8000/speak --output response.mp3
    """
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI TTS non disponible. OPENAI_API_KEY non configurée."
        )

    try:
        # Appeler l'API OpenAI TTS
        response = openai_client.audio.speech.create(
            model="gpt-4o-audio-preview",
            voice="alloy",
            input=request.text
        )

        # Récupérer le contenu audio
        audio_content = response.content

        # Retourner le fichier MP3
        return StreamingResponse(
            io.BytesIO(audio_content),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="speech.mp3"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération audio: {str(e)}"
        )

@app.post("/speak/google")
async def speak_google(request: SpeakRequest):
    """
    Génère de l'audio depuis du texte en utilisant Google Cloud TTS

    Usage: POST /speak/google avec JSON {"text": "votre texte"}
    Retourne: Fichier audio MP3

    Exemple:
        curl -X POST -H "Content-Type: application/json" \
             -d '{"text":"Bonjour et bienvenue!"}' \
             http://localhost:8000/speak/google --output response.mp3
    """
    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Google Cloud TTS non disponible. GOOGLE_API_KEY non configurée."
        )

    try:
        # Construire la requête pour Google Cloud TTS API
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_API_KEY}"

        payload = {
            "input": {
                "text": request.text
            },
            "voice": {
                "languageCode": "fr-FR",
                "name": "fr-FR-Wavenet-A",  # Voix masculine
                "ssmlGender": "MALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,
                "pitch": 0.0
            }
        }

        # Appeler l'API Google Cloud TTS
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", "Erreur inconnue")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur Google Cloud TTS: {error_msg}"
            )

        # Récupérer le contenu audio encodé en base64
        audio_base64 = response.json().get("audioContent")
        if not audio_base64:
            raise HTTPException(
                status_code=500,
                detail="Pas de contenu audio dans la réponse"
            )

        # Décoder le base64 pour obtenir le fichier MP3
        audio_content = base64.b64decode(audio_base64)

        # Retourner le fichier MP3
        return StreamingResponse(
            io.BytesIO(audio_content),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="speech_google.mp3"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération audio: {str(e)}"
        )

@app.get("/health")
def health():
    return {
        "status": "ok",
        "platform": "Raspberry Pi 5",
        "llm_provider": "Groq API",
        "llm_model": runtime_settings.get("llm_model", GROQ_MODEL),
        "stt_engine": runtime_settings.get("stt_engine", STT_ENGINE),
        "tts_engine": runtime_settings.get("tts_engine", TTS_ENGINE),
        "capabilities": ["voice", "text", "multilingual"]
    }

@app.get("/capabilities")
def capabilities():
    """Liste les capacités de l'assistant"""
    return {
        "stt": {
            "engines": ["whisper", "vosk", "faster-whisper"],
            "current": runtime_settings.get("stt_engine", STT_ENGINE),
            "models": {
                "whisper": WHISPER_MODEL,
                "vosk": VOSK_MODEL_PATH if Path(VOSK_MODEL_PATH).exists() else "not installed"
            },
            "languages": ["fr", "moore", "dioula", "fulfulde"]
        },
        "tts": {
            "engines": ["piper", "espeak"],
            "current": runtime_settings.get("tts_engine", TTS_ENGINE),
            "voices": {
                "fr": "native",
                "moore": "fallback",
                "dioula": "fallback"
            },
            "cache": {
                "enabled": True,
                "directory": str(TTS_CACHE_DIR),
                "stats": tts_cache_stats
            }
        },
        "llm": {
            "provider": "Groq API",
            "model": GROQ_MODEL,
            "context_window": 8192
        },
        "rag": {
            "index_size": faiss_index.ntotal,
            "top_k": TOP_K
        }
    }

@app.get("/stats")
def stats():
    """Statistiques système"""
    import psutil
    mem = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=None)
    snapshot = get_metrics_snapshot()
    return {
        "ram_total_gb": round(mem.total / 1024**3, 2),
        "ram_used_gb": round(mem.used / 1024**3, 2),
        "ram_available_gb": round(mem.available / 1024**3, 2),
        "ram_percent": mem.percent,
        "cpu_percent": cpu_percent,
        "faiss_vectors": faiss_index.ntotal,
        "custom_vectors": custom_index.ntotal if custom_index else 0,
        "stt_engine": STT_ENGINE,
        "tts_engine": TTS_ENGINE,
        "stt_loaded": whisper_model is not None or vosk_model is not None,
        "requests": snapshot
    }

# ----- DOCUMENTATION -----
@app.get("/")
def root():
    return {
        "name": "Assistant Vocal Orange Burkina Faso",
        "version": "1.0.0",
        "description": "Assistant vocal complet avec STT + RAG + TTS",
        "endpoints": {
            "POST /voice/ask": "Question vocale → Réponse vocale/texte",
            "POST /voice/transcribe": "Audio → Texte (STT uniquement)",
            "POST /text/ask": "Question texte → Réponse texte/audio",
            "GET /tts": "Texte → Audio (TTS uniquement)",
            "GET /health": "État du serveur",
            "GET /capabilities": "Capacités de l'assistant",
            "GET /stats": "Statistiques système"
        },
        "documentation": "/docs"
    }
