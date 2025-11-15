import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Fichier contenant les paragraphes (créé par ton script précédent)
input_file = "orange_services_paragraphs.json"
index_file = "orange_faq.index"
metadata_file = "metadata.json"

# Charger le modèle léger
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Charger les paragraphes
with open(input_file, "r") as f:
    data = json.load(f)  # ✅ lecture correcte du JSON complet

texts = [item["text"] for item in data if "text" in item]

# Générer les embeddings
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

# Normalisation pour améliorer la recherche cosine
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

# Créer un index FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)

# Sauvegarder l’index et les métadonnées
faiss.write_index(index, index_file)

with open(metadata_file, "w") as f:
    json.dump(texts, f, ensure_ascii=False, indent=2)

print(f"✅ Index créé avec {len(texts)} paragraphes et sauvegardé dans {index_file}")

