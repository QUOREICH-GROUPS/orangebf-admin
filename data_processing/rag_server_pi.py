# rag_server_pi.py
# Optimized for Raspberry Pi 5 (ARM64, 8GB RAM)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from llama_cpp import Llama

app = FastAPI(title="RAG Chatbot - Orange Faso (Raspberry Pi 5)")

# ----- CONFIG OPTIMISÉE POUR PI -----
INDEX_FILE = "orange_faq.index"
METADATA_FILE = "metadata.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Léger: ~80MB
TOP_K = 3  # Réduit pour économiser le contexte

# Modèles recommandés pour Pi 5 (par ordre de préférence):
# 1. Phi-3-mini Q4: ~2.3GB RAM, excellente qualité, rapide
# 2. TinyLlama Q4: ~800MB RAM, très rapide, qualité correcte
# 3. Llama-3.2-3B Q4: ~2GB RAM, bon équilibre
MODEL_PATH = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # TinyLlama for testing

# ----- CHARGEMENT DES RESSOURCES -----
print("🔄 Chargement du modèle d'embeddings...")
embed_model = SentenceTransformer(EMBEDDING_MODEL)

print("🔄 Chargement de l'index FAISS...")
if not Path(INDEX_FILE).exists() or not Path(METADATA_FILE).exists():
    raise FileNotFoundError("Index ou metadata non trouvés.")

faiss_index = faiss.read_index(INDEX_FILE)

with open(METADATA_FILE, "r") as f:
    texts = json.load(f)

print("🔄 Chargement du LLM (cela peut prendre 30-60 secondes)...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,        # Contexte réduit pour économiser la RAM
    n_threads=4,       # Pi 5 a 4 cores
    n_batch=256,       # Batch size optimisé pour ARM
    n_gpu_layers=0,    # Pas de GPU sur Pi
    use_mmap=True,     # Utilise mmap pour économiser la RAM
    use_mlock=False,   # Ne pas verrouiller en RAM (économise de la mémoire)
    verbose=False
)

print("✅ Serveur prêt!")

# ----- SCHEMA -----
class QuestionRequest(BaseModel):
    question: str

# ----- UTIL -----
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
        max_tokens=200,      # Limité pour la vitesse
        temperature=0.1,     # Très factuel
        top_p=0.9,
        repeat_penalty=1.1,
        stop=["<|end|>", "<|user|>"],
        echo=False
    )

    return response['choices'][0]['text'].strip()

# ----- ENDPOINTS -----
@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    passages, scores = retrieve_context(question)
    response_text = generate_response(question, passages)

    return {
        "question": question,
        "retrieved_passages": passages,
        "scores": scores.tolist(),
        "response": response_text,
        "model": "phi-3-mini-q4 (Pi optimized)"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "platform": "Raspberry Pi 5",
        "model": MODEL_PATH
    }

@app.get("/stats")
def stats():
    """Statistiques d'utilisation mémoire"""
    import psutil
    mem = psutil.virtual_memory()
    return {
        "ram_total_gb": round(mem.total / 1024**3, 2),
        "ram_used_gb": round(mem.used / 1024**3, 2),
        "ram_available_gb": round(mem.available / 1024**3, 2),
        "ram_percent": mem.percent,
        "faiss_vectors": faiss_index.ntotal
    }
