# rag_server_openai.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import os
from openai import OpenAI

app = FastAPI(title="RAG Chatbot - Orange Faso avec OpenAI")

# ----- CONFIG -----
INDEX_FILE = "orange_faq.index"
METADATA_FILE = "metadata.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5

# ----- CHARGEMENT DES RESSOURCES -----
embed_model = SentenceTransformer(EMBEDDING_MODEL)

if not Path(INDEX_FILE).exists() or not Path(METADATA_FILE).exists():
    raise FileNotFoundError("Index ou metadata non trouvés.")

faiss_index = faiss.read_index(INDEX_FILE)

with open(METADATA_FILE, "r") as f:
    texts = json.load(f)

# OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def generate_response_openai(question: str, passages: list):
    context = "\n\n".join(passages)

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4o" for better quality
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant virtuel pour Orange Burkina Faso. Réponds aux questions des clients de manière claire, précise et professionnelle en te basant sur le contexte fourni. Si l'information n'est pas dans le contexte, dis-le poliment."
            },
            {
                "role": "user",
                "content": f"Contexte:\n{context}\n\nQuestion: {question}\n\nRéponse:"
            }
        ],
        temperature=0.3,
        max_tokens=500
    )

    return response.choices[0].message.content

# ----- ENDPOINTS -----
@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    passages, scores = retrieve_context(question)
    response_text = generate_response_openai(question, passages)

    return {
        "question": question,
        "retrieved_passages": passages,
        "scores": scores.tolist(),
        "response": response_text
    }

@app.get("/health")
def health():
    return {"status": "ok", "model": "gpt-4o-mini"}
