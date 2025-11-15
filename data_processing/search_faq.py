# search_faq.py
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from local_knowledge import get_fact

# --- Config ---
index_file = "orange_faq.index"
metadata_file = "metadata.json"
model_name = "sentence-transformers/all-MiniLM-L6-v2"
top_k = 5

# Charger l'index FAISS et les métadonnées
index = faiss.read_index(index_file)
with open(metadata_file, "r") as f:
    texts = json.load(f)

# Charger le modèle
model = SentenceTransformer(model_name)

def search_faq(query):
    embedding = model.encode([query], convert_to_numpy=True)
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
    D, I = index.search(embedding, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        results.append({"text": texts[idx], "score": float(score)})
    return results

import sys

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search_faq(query)
        print(f"\n🔎 Résultats pour : {query}\n")
        for i, r in enumerate(results, start=1):
            snippet = r['text'][:200].replace("\n", " ") + ("..." if len(r['text']) > 200 else "")
            print(f"{i}. {snippet}\n→ Score : {r['score']:.4f}\n")
        return

    print("💡 FAQ Orange Money & Connaissance locale")
    print("Tapez 'exit' pour quitter.\n")
    
    while True:
        query = input("Pose ta question : ").strip()
        if query.lower() == "exit":
            break
        
        # Vérifier si la question correspond à un fait local
        local_answer = get_fact(query)
        if local_answer:
            if isinstance(local_answer, dict) and "hymne" in local_answer:
                # Si hymne, demander la langue
                print("Dans quelle langue ? (francais/moore/dioula)")
                lang = input("Langue : ").strip().lower()
                hymne = local_answer.get(lang, "Désolé, langue non disponible.")
                print(f"\n🎵 Hymne national ({lang}) :\n{hymne}\n")
            else:
                print(f"\n💡 Réponse locale : {local_answer}\n")
            continue
        
        # Sinon, recherche FAISS
        results = search_faq(query)
        print(f"\n🔎 Résultats pour : {query}\n")
        for i, r in enumerate(results, start=1):
            snippet = r['text'][:200].replace("\n", " ") + ("..." if len(r['text']) > 200 else "")
            print(f"{i}. {snippet}\n→ Score : {r['score']:.4f}\n")

if __name__ == "__main__":
    main()

