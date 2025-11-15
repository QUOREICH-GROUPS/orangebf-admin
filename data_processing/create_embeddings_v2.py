#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_embeddings_v2.py - Création d'embeddings à partir des données nettoyées v2
"""

import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Fichiers
input_file = "orange_services_clean_v2.json"
index_file = "orange_faq_v2.index"
metadata_file = "metadata_v2.json"

print("=" * 60)
print("🔧 CRÉATION DES EMBEDDINGS - VERSION 2 (DONNÉES PROPRES)")
print("=" * 60)

# Charger le modèle léger
print("\n📦 Chargement du modèle d'embeddings...")
print("   Modèle: sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("✅ Modèle chargé")

# Charger les paragraphes nettoyés
print(f"\n📂 Chargement de {input_file}...")
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [item["text"] for item in data if "text" in item and len(item["text"]) > 10]

print(f"✅ {len(texts)} paragraphes chargés")
print(f"   Longueur moyenne: {sum(len(t) for t in texts) / len(texts):.0f} caractères")

# Générer les embeddings
print("\n🔄 Génération des embeddings...")
print("   (Cela peut prendre quelques minutes...)")
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
print(f"✅ Embeddings générés: {embeddings.shape}")

# Normalisation pour améliorer la recherche cosine similarity
print("\n🔧 Normalisation des embeddings...")
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
print("✅ Embeddings normalisés")

# Créer un index FAISS (IndexFlatIP = Inner Product, pour cosine similarity)
print("\n📊 Création de l'index FAISS...")
dimension = embeddings.shape[1]
print(f"   Dimension: {dimension}")
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)
print(f"✅ Index créé avec {index.ntotal} vecteurs")

# Sauvegarder l'index
print(f"\n💾 Sauvegarde de l'index dans {index_file}...")
faiss.write_index(index, index_file)
print("✅ Index sauvegardé")

# Sauvegarder les métadonnées (textes)
print(f"\n💾 Sauvegarde des métadonnées dans {metadata_file}...")
with open(metadata_file, "w", encoding="utf-8") as f:
    json.dump(texts, f, ensure_ascii=False, indent=2)
print("✅ Métadonnées sauvegardées")

# Statistiques finales
print("\n" + "=" * 60)
print("📊 STATISTIQUES FINALES")
print("=" * 60)
print(f"   Paragraphes indexés: {len(texts)}")
print(f"   Dimension des vecteurs: {dimension}")
print(f"   Taille de l'index: {index.ntotal} vecteurs")
print(f"   Fichier index: {index_file}")
print(f"   Fichier metadata: {metadata_file}")
print("=" * 60)
print("✅ INDEXATION TERMINÉE AVEC SUCCÈS!")
print("=" * 60)

# Exemples de recherche pour vérification
print("\n🧪 Test de recherche...")
test_queries = [
    "Comment consulter mon solde?",
    "Activer Orange Money",
    "Forfait internet"
]

for query in test_queries:
    q_vec = model.encode([query], convert_to_numpy=True)
    q_vec = q_vec / np.linalg.norm(q_vec, axis=1, keepdims=True)
    scores, indices = index.search(q_vec, 3)

    print(f"\n🔍 Query: '{query}'")
    print(f"   Top 3 résultats:")
    for i, (idx, score) in enumerate(zip(indices[0], scores[0]), 1):
        text_preview = texts[idx][:80] + "..." if len(texts[idx]) > 80 else texts[idx]
        print(f"      {i}. (score: {score:.3f}) {text_preview}")

print("\n" + "=" * 60)
print("✅ Système RAG prêt à l'emploi!")
print("=" * 60)
