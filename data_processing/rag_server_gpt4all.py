# rag_server_gpt4all.py
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import tempfile
import os
from groq import Groq
import edge_tts
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

app = FastAPI(title="RAG Chatbot - Orange Faso (Groq + Edge-TTS)")

# Activer CORS pour l'interface web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer le dossier pour les fichiers audio statiques
os.makedirs("static/audio", exist_ok=True)

# Monter le dossier static pour servir les fichiers audio
app.mount("/audio", StaticFiles(directory="static/audio"), name="audio")

# Charger l'index audio des hymnes nationaux
AUDIO_INDEX_FILE = "audio_index.json"
audio_index = {}
try:
    if os.path.exists(AUDIO_INDEX_FILE):
        with open(AUDIO_INDEX_FILE, 'r', encoding='utf-8') as f:
            audio_index = json.load(f)
        print(f"✅ Index audio chargé: {len(audio_index)} fichiers audio disponibles")
    else:
        print(f"⚠️  Fichier {AUDIO_INDEX_FILE} non trouvé - versions audio de l'hymne non disponibles")
except Exception as e:
    print(f"⚠️  Erreur lors du chargement de l'index audio: {e}")

# ----- CONFIG -----
INDEX_FILE = "orange_faq.index"
METADATA_FILE = "metadata.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5  # nombre de passages à récupérer

# Groq Configuration (Gratuit et ULTRA RAPIDE !)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️  GROQ_API_KEY non définie - le système ne fonctionnera pas")
    groq_client = None
else:
    groq_client = Groq(api_key=GROQ_API_KEY)

# Modèle Groq pour la génération de texte (ultra rapide)
GROQ_MODEL = "llama-3.1-8b-instant"  # Le plus rapide !

# Voice settings
WHISPER_MODEL = "whisper-large-v3"  # Modèle Groq Whisper (gratuit)
# Edge-TTS Voices (Gratuit, Microsoft)
# Options voix masculines françaises: fr-FR-HenriNeural, fr-FR-AlainNeural, fr-FR-ClaudeNeural
# Options voix féminines françaises: fr-FR-DeniseNeural, fr-FR-EloiseNeural
TTS_VOICE = "fr-FR-HenriNeural"  # Voix masculine professionnelle par défaut

# ----- CHARGEMENT DES RESSOURCES -----
# Embeddings
embed_model = SentenceTransformer(EMBEDDING_MODEL)

# FAISS index
if not Path(INDEX_FILE).exists() or not Path(METADATA_FILE).exists():
    raise FileNotFoundError("Index ou metadata non trouvés. Créez-les avant de lancer le serveur.")

faiss_index = faiss.read_index(INDEX_FILE)

# Metadata
with open(METADATA_FILE, "r") as f:
    texts = json.load(f)

# ----- SCHEMA DE REQUÊTE -----
class QuestionRequest(BaseModel):
    question: str

class SpeakRequest(BaseModel):
    text: str
    voice: str = "fr-FR-HenriNeural"  # Voix Edge-TTS
    # Options voix masculines: fr-FR-HenriNeural, fr-FR-AlainNeural, fr-FR-ClaudeNeural
    # Options voix féminines: fr-FR-DeniseNeural, fr-FR-EloiseNeural, fr-FR-BrigitteNeural

class TextAskRequest(BaseModel):
    question: str
    language: str = "fr"
    enable_voice: bool = True

# ----- CONNAISSANCES LOCALES -----
LOCAL_KNOWLEDGE = {
    "president": "Le président du Burkina Faso est Ibrahim Traoré.",
    "hymne_francais": """L'Hymne National du Burkina Faso, LE DITANYÉ :

Contre la férule humiliante il y a déjà mille ans,
La rapacité venue de loin les asservir il y a cent ans.
Contre la cynique malice métamorphosée
En néocolonialisme et ses petits servants locaux
Beaucoup flanchèrent et certains résistèrent.

REFRAIN :
Et une seule nuit a rassemblé en elle
L'histoire de tout un peuple.
Et une seule nuit a déclenché sa marche triomphale
Vers l'horizon du bonheur.
Une seule nuit a réconcilié notre peuple
Avec tous les peuples du monde,
À la conquête de la liberté et du progrès
La Patrie ou la mort, nous vaincrons !""",
    "salutations_moore": {
        "bonjour": "Yibéogo !",
        "comment_ca_va": "Kibaré ?",
        "ca_va": "Laafi",
        "merci": "Barka"
    },
    "salutations_dioula": {
        "bonjour": "Inché",
        "comment_ca_va": "Djam na ?",
        "ca_va": "Djam tan",
        "merci": "I ni tché"
    },
    "orange_money_activation": """Pour activer Orange Money, voici les étapes simples :

1. Vous devez être abonné chez Orange avec une ligne identifiée à votre nom.
2. Rendez-vous dans une boutique Orange ou chez un distributeur agréé Orange Money.
3. Munissez-vous d'une pièce d'identité (CNIB, passeport, Carte Consulaire, Carte militaire).
4. Remplissez le formulaire de souscription.
5. L'agent distributeur créera votre compte Orange Money.
6. Dès que vous changez le code PIN par défaut (1234), votre compte devient actif.

Ensuite, pour utiliser Orange Money :
- Composez *144# et suivez les instructions
- Ou téléchargez l'application Orange Money sur Play Store

Le service est disponible 24h/24 et 7j/7. Pour toute assistance, appelez le 127 ou le 121.""",
    "orange_money_info": """Orange Money est un système de paiement électronique qui permet d'effectuer des transactions financières à l'aide du téléphone portable.

Avec Orange Money, vous pouvez :
- Transférer et recevoir de l'argent
- Recharger des crédits d'appels
- Payer des factures (SONABEL, ONEA, etc.)
- Effectuer des abonnements TV (Canal+, DSTV)
- Payer des biens et services
- Accéder à votre compte bancaire (si disponible)

Pour utiliser le service : *144# ou l'application Orange Money.""",
    "paiement_factures": """Pour payer vos factures avec Orange Money :

**SONABEL (Électricité) :**
- Composez *144# et suivez le menu
- Ou utilisez l'application Max it
- Frais : 100 FCFA (factures 1-2000 FCFA), 150 FCFA (2001-10000 FCFA), 200 FCFA (10001-500000 FCFA)

**ONEA (Eau) :**
- Composez *144# et suivez le menu
- Ou utilisez l'application Max it
- Mêmes frais que SONABEL

**Canal+ / DSTV :**
- Via *144# ou l'application Orange Money
- Paiement gratuit

Pour toute assistance : appelez le 127 ou le 121."""
}

def check_local_knowledge(question: str):
    """Vérifie si la question concerne des connaissances locales hardcodées"""
    question_lower = question.lower()

    # Président
    if any(word in question_lower for word in ["président", "president", "chef d'état", "chef etat"]):
        return LOCAL_KNOWLEDGE["president"]

    # Hymne national
    if any(word in question_lower for word in ["hymne", "ditanyé", "ditanye", "chante", "chanson nationale"]):
        # Détecter la langue demandée
        langue_detectee = None
        audio_url = None

        if any(word in question_lower for word in ["moore", "mooré", "moré"]):
            langue_detectee = "moore"
        elif any(word in question_lower for word in ["dioula", "jula"]):
            langue_detectee = "dioula"
        elif any(word in question_lower for word in ["fulfulde", "peul", "fula"]):
            langue_detectee = "fulfulde"
        elif any(word in question_lower for word in ["français", "francais", "french"]):
            langue_detectee = "francais"

        hymne_response = LOCAL_KNOWLEDGE["hymne_francais"]

        # Si une langue est détectée et qu'on a l'audio
        if langue_detectee and langue_detectee in audio_index:
            audio_url = f"http://localhost:8000/audio/{audio_index[langue_detectee]['filename']}"
            hymne_response += f"\n\n🎵 **Version audio en {audio_index[langue_detectee]['langue'].title()}** :\n"
            hymne_response += f"▶️ AUDIO: {audio_url}"
            # Retourner un dict pour que l'endpoint puisse gérer l'audio
            return {"text": hymne_response, "audio_url": audio_url, "langue": langue_detectee}
        elif langue_detectee == "francais":
            # Pas d'audio en français, juste le texte
            return {"text": hymne_response}
        else:
            # Pas de langue spécifiée, demander de préciser
            if audio_index:
                hymne_response += "\n\n🎵 **Versions audio disponibles** :\n"
                hymne_response += "Veuillez préciser la langue souhaitée :\n"
                if "moore" in audio_index:
                    hymne_response += f"- En Moore : dites 'hymne en moore'\n"
                if "dioula" in audio_index:
                    hymne_response += f"- En Dioula : dites 'hymne en dioula'\n"
                if "fulfulde" in audio_index:
                    hymne_response += f"- En Fulfulde : dites 'hymne en fulfulde'\n"

            return {"text": hymne_response}

    # Orange Money - Activation
    if "orange money" in question_lower or "orange-money" in question_lower or "orangemoney" in question_lower:
        if any(word in question_lower for word in ["activer", "activation", "ouvrir", "créer", "souscrire", "comment", "*144"]):
            return LOCAL_KNOWLEDGE["orange_money_activation"]
        # Orange Money - Info générale
        elif any(word in question_lower for word in ["c'est quoi", "qu'est-ce", "définition", "utiliser", "faire"]):
            return LOCAL_KNOWLEDGE["orange_money_info"]

    # Paiement de factures (SONABEL, ONEA, Canal+)
    if any(word in question_lower for word in ["payer", "paiement", "facture", "sonabel", "onea", "canal+", "dstv"]):
        if any(service in question_lower for service in ["sonabel", "onea", "canal", "électricité", "electricite", "eau", "compteur"]):
            return LOCAL_KNOWLEDGE["paiement_factures"]

    # Salutations en Mooré
    if "mooré" in question_lower or "moore" in question_lower:
        if "bonjour" in question_lower:
            return f"En Mooré, on dit : {LOCAL_KNOWLEDGE['salutations_moore']['bonjour']}"
        elif "comment" in question_lower and "va" in question_lower:
            return f"En Mooré, on dit : {LOCAL_KNOWLEDGE['salutations_moore']['comment_ca_va']}"

    # Salutations en Dioula
    if "dioula" in question_lower:
        if "bonjour" in question_lower:
            return f"En Dioula, on dit : {LOCAL_KNOWLEDGE['salutations_dioula']['bonjour']}"
        elif "comment" in question_lower and "va" in question_lower:
            return f"En Dioula, on dit : {LOCAL_KNOWLEDGE['salutations_dioula']['comment_ca_va']}"

    return None

# ----- UTIL -----
def retrieve_context(query: str, top_k: int = TOP_K):
    q_vec = embed_model.encode([query], convert_to_numpy=True)
    q_vec = q_vec / np.linalg.norm(q_vec, axis=1, keepdims=True)
    scores, indices = faiss_index.search(q_vec, top_k)
    passages = [texts[i] for i in indices[0]]
    return passages, scores[0]

def generate_response(question: str, passages: list):
    """Génère une réponse avec Groq LLaMA 3.1 (ultra rapide!)"""
    if not groq_client:
        return "Erreur: Service de génération non disponible (GROQ_API_KEY manquante)"

    context = "\n\n".join(passages)

    # Prompt optimisé pour Groq
    messages = [
        {
            "role": "system",
            "content": "Tu es un assistant virtuel pour Orange Burkina Faso. Réponds de manière claire, concise et professionnelle en utilisant UNIQUEMENT les informations du contexte fourni. Si l'information n'est pas dans le contexte, dis 'Je n'ai pas cette information dans ma base de données.'"
        },
        {
            "role": "user",
            "content": f"""Contexte:
{context}

Question: {question}

Réponds de manière claire et concise en te basant uniquement sur le contexte ci-dessus."""
        }
    ]

    try:
        # Appel à Groq (ultra rapide!)
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=300,
            top_p=1,
            stream=False
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"Erreur lors de la génération: {str(e)}"

# ----- ENDPOINTS -----
@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    # Vérifier d'abord les connaissances locales
    local_answer = check_local_knowledge(question)
    if local_answer:
        # Gérer le nouveau format avec audio (dict) ou ancien format (string)
        if isinstance(local_answer, dict):
            response_data = {
                "question": question,
                "retrieved_passages": [],
                "scores": [],
                "response": local_answer.get("text", local_answer)
            }
            # Ajouter l'URL audio si disponible
            if "audio_url" in local_answer:
                response_data["audio_url"] = local_answer["audio_url"]
                response_data["audio_langue"] = local_answer.get("langue", "")
            return response_data
        else:
            # Ancien format (string)
            return {
                "question": question,
                "retrieved_passages": [],
                "scores": [],
                "response": local_answer
            }

    # Sinon, utiliser FAISS + Groq
    passages, scores = retrieve_context(question)
    response_text = generate_response(question, passages)

    return {
        "question": question,
        "retrieved_passages": passages,
        "scores": scores.tolist(),
        "response": response_text
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/hymne-audio")
def get_hymne_audio():
    """
    Retourne la liste des versions audio de l'hymne national disponibles
    """
    if not audio_index:
        return {
            "available": False,
            "message": "Aucune version audio disponible",
            "hymnes": []
        }

    hymnes = []
    for audio_id, audio_data in audio_index.items():
        hymnes.append({
            "id": audio_id,
            "langue": audio_data.get("langue", ""),
            "description": audio_data.get("description", ""),
            "url": f"http://localhost:8000/audio/{audio_data['filename']}",
            "taille_mb": audio_data.get("size_mb", 0)
        })

    return {
        "available": True,
        "count": len(hymnes),
        "hymnes": hymnes
    }

# ----- VOICE ENDPOINTS -----

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Convertit un fichier audio en texte avec Groq Whisper (GRATUIT).
    Supporte: mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB)
    """
    if not groq_client:
        raise HTTPException(status_code=503, detail="Service vocal non disponible. GROQ_API_KEY non configurée.")

    # Vérifier le type de fichier
    allowed_types = ["audio/mpeg", "audio/mp4", "audio/mpeg", "audio/mpga", "audio/m4a", "audio/wav", "audio/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Type de fichier non supporté: {file.content_type}")

    try:
        # Sauvegarder temporairement le fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Transcription avec Groq Whisper (gratuit et rapide!)
        with open(tmp_file_path, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                language="fr",  # Force le français pour de meilleurs résultats
                response_format="text"
            )

        # Nettoyer le fichier temporaire
        os.unlink(tmp_file_path)

        return {
            "text": transcript,
            "filename": file.filename
        }

    except Exception as e:
        # Nettoyer en cas d'erreur
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Erreur de transcription: {str(e)}")


@app.post("/speak")
async def text_to_speech(request: SpeakRequest):
    """
    Convertit du texte en audio avec Edge-TTS (GRATUIT, Microsoft).
    Retourne un fichier MP3.
    Voix par défaut: fr-FR-HenriNeural (masculine, professionnelle)
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte ne peut pas être vide")

    try:
        # Utiliser la voix demandée ou la voix par défaut
        voice = request.voice if request.voice else TTS_VOICE

        # Créer un fichier temporaire pour l'audio
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_file_path = tmp_file.name
        tmp_file.close()

        # Générer l'audio avec Edge-TTS (gratuit!)
        communicate = edge_tts.Communicate(request.text, voice)
        await communicate.save(tmp_file_path)

        # Retourner le fichier audio
        return FileResponse(
            tmp_file_path,
            media_type="audio/mpeg",
            filename="response.mp3",
            background=None
        )

    except Exception as e:
        # Nettoyer en cas d'erreur
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Erreur TTS: {str(e)}")


@app.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)):
    """
    Endpoint complet: reçoit un audio, le transcrit, génère une réponse RAG,
    et retourne la réponse en audio (TOUT GRATUIT avec Groq + Edge-TTS).

    Flow: Audio (question) -> Texte -> RAG -> Réponse texte -> Audio (réponse)
    """
    if not groq_client:
        raise HTTPException(status_code=503, detail="Service vocal non disponible. GROQ_API_KEY non configurée.")

    try:
        # 1. Transcription de la question audio avec Groq Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_input:
            content = await file.read()
            tmp_input.write(content)
            tmp_input_path = tmp_input.name

        with open(tmp_input_path, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                language="fr",
                response_format="text"
            )

        question = transcript
        os.unlink(tmp_input_path)

        # 2. Génération de la réponse RAG
        passages, scores = retrieve_context(question)
        response_text = generate_response(question, passages)

        # 3. Conversion de la réponse en audio avec Edge-TTS
        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_output_path = tmp_output.name
        tmp_output.close()

        communicate = edge_tts.Communicate(response_text, TTS_VOICE)
        await communicate.save(tmp_output_path)

        # Retourner l'audio de la réponse
        return FileResponse(
            tmp_output_path,
            media_type="audio/mpeg",
            filename="chat_response.mp3",
            headers={
                "X-Question-Text": question,
                "X-Response-Text": response_text[:200]  # Limité pour éviter les problèmes d'en-tête
            }
        )

    except Exception as e:
        # Nettoyer les fichiers temporaires en cas d'erreur
        if 'tmp_input_path' in locals() and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if 'tmp_output_path' in locals() and os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)
        raise HTTPException(status_code=500, detail=f"Erreur voice-chat: {str(e)}")


# ----- ENDPOINTS POUR L'INTERFACE WEB EXISTANTE -----

@app.post("/text/ask")
async def text_ask(request: TextAskRequest):
    """
    Endpoint compatible avec l'interface web existante (port 3000).
    Génère une réponse texte RAG + optionnellement un audio TTS.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    try:
        # 1. Vérifier d'abord les connaissances locales
        local_answer = check_local_knowledge(question)
        audio_prerecorded = None  # Pour l'hymne audio pré-enregistré

        if local_answer:
            # Gérer le nouveau format avec audio (dict) ou ancien format (string)
            if isinstance(local_answer, dict):
                response_text = local_answer.get("text", "")
                # Vérifier si on a un audio pré-enregistré
                if "audio_url" in local_answer:
                    audio_prerecorded = local_answer["audio_url"]
            else:
                response_text = local_answer
        else:
            # Sinon, utiliser FAISS + Groq
            passages, scores = retrieve_context(question)
            response_text = generate_response(question, passages)

        # 2. Préparer la réponse de base
        response_data = {
            "type": "text",
            "text": response_text,
            "response": response_text
        }

        # 3. Gérer l'audio
        if request.enable_voice:
            # Si on a un audio pré-enregistré (hymne), l'utiliser directement
            if audio_prerecorded:
                response_data["tts_url"] = audio_prerecorded.replace("http://localhost:8000", "")
            else:
                try:
                    # Créer fichier temporaire pour le TTS
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                    tmp_file_path = tmp_file.name
                    tmp_file.close()

                    # Générer audio avec Edge-TTS
                    communicate = edge_tts.Communicate(response_text, TTS_VOICE)
                    await communicate.save(tmp_file_path)

                    # Sauvegarder dans un dossier accessible
                    import shutil
                    tts_filename = f"tts_{hash(question)}.mp3"
                    tts_path = f"static/audio/{tts_filename}"
                    os.makedirs("static/audio", exist_ok=True)
                    shutil.copy(tmp_file_path, tts_path)
                    os.unlink(tmp_file_path)

                    response_data["tts_url"] = f"/audio/{tts_filename}"

                except Exception as e:
                    print(f"Erreur TTS: {e}")
                    # Continue sans TTS en cas d'erreur

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.post("/voice/ask")
async def voice_ask(
    audio: UploadFile = File(...),
    language: str = "fr",
    response_format: str = "both"
):
    """
    Endpoint compatible avec l'interface web existante (port 3000).
    Transcrit l'audio, génère une réponse RAG, et retourne texte + audio.
    """
    if not groq_client:
        raise HTTPException(status_code=503, detail="Service vocal non disponible. GROQ_API_KEY non configurée.")

    try:
        # 1. Transcription avec Groq Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as tmp_input:
            content = await audio.read()
            tmp_input.write(content)
            tmp_input_path = tmp_input.name

        with open(tmp_input_path, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                language="fr",
                response_format="text"
            )

        question = transcript
        os.unlink(tmp_input_path)

        # 2. Génération de la réponse RAG
        passages, scores = retrieve_context(question)
        response_text = generate_response(question, passages)

        # 3. Générer audio de réponse avec Edge-TTS
        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_output_path = tmp_output.name
        tmp_output.close()

        communicate = edge_tts.Communicate(response_text, TTS_VOICE)
        await communicate.save(tmp_output_path)

        # 4. Convertir en base64 pour la réponse
        import base64
        with open(tmp_output_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')

        os.unlink(tmp_output_path)

        return {
            "question": question,
            "response": response_text,
            "audio_base64": audio_base64
        }

    except Exception as e:
        # Nettoyer fichiers temporaires
        if 'tmp_input_path' in locals() and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if 'tmp_output_path' in locals() and os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
