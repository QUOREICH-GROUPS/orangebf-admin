# Intégration Audio de l'Hymne National - Système RAG Orange Burkina Faso

**Date**: 2025-11-14
**Statut**: ✅ Opérationnel

---

## 🎵 Vue d'Ensemble

Le système RAG intègre maintenant 3 versions audio officielles de l'hymne national du Burkina Faso "LE DITANYÉ" en langues locales:

| Langue | Fichier | Taille | URL |
|--------|---------|--------|-----|
| **Moore** | moore.mp3 | 3.34 MB | http://localhost:8000/audio/moore.mp3 |
| **Dioula** | dioula.mp3 | 2.81 MB | http://localhost:8000/audio/dioula.mp3 |
| **Fulfulde** | fulfulde.mp3 | 2.41 MB | http://localhost:8000/audio/fulfulde.mp3 |

---

## 📁 Structure des Fichiers

```
orangebf/
├── static/
│   └── audio/
│       ├── moore.mp3          # Hymne en Moore (3.4 MB)
│       ├── dioula.mp3         # Hymne en Dioula (2.9 MB)
│       └── fulfulde.mp3       # Hymne en Fulfulde (2.5 MB)
├── audio_index.json           # Index des métadonnées audio
├── create_audio_index.py      # Script de génération d'index
└── data_processing/
    └── rag_server_gpt4all.py  # Serveur RAG (modifié)
```

---

## ⚙️ Modifications Apportées

### 1. Chargement de l'Index Audio au Démarrage

**Fichier**: `data_processing/rag_server_gpt4all.py` (lignes 39-50)

```python
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
```

### 2. Modification de la Réponse Hymne National

**Fonction**: `check_local_knowledge()` (lignes 190-203)

```python
# Hymne national
if any(word in question_lower for word in ["hymne", "ditanyé", "ditanye", "chante", "chanson nationale"]):
    hymne_response = LOCAL_KNOWLEDGE["hymne_francais"]

    # Ajouter les liens vers les versions audio si disponibles
    if audio_index:
        hymne_response += "\n\n🎵 **Versions audio disponibles** :\n"
        if "moore" in audio_index:
            hymne_response += f"- En Moore : http://localhost:8000/audio/moore.mp3\n"
        if "dioula" in audio_index:
            hymne_response += f"- En Dioula : http://localhost:8000/audio/dioula.mp3\n"
        if "fulfulde" in audio_index:
            hymne_response += f"- En Fulfulde : http://localhost:8000/audio/fulfulde.mp3\n"

    return hymne_response
```

### 3. Nouvel Endpoint API

**Endpoint**: `GET /hymne-audio` (lignes 314-340)

```python
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
```

---

## 🧪 Tests et Validation

### Test 1: Endpoint `/hymne-audio`

```bash
curl http://localhost:8000/hymne-audio
```

**Résultat**:
```json
{
  "available": true,
  "count": 3,
  "hymnes": [
    {
      "id": "moore",
      "langue": "moore",
      "description": "Version officielle de l'hymne national Le Ditanyé en Moore",
      "url": "http://localhost:8000/audio/moore.mp3",
      "taille_mb": 3.34
    },
    {
      "id": "dioula",
      "langue": "dioula",
      "description": "Version officielle de l'hymne national Le Ditanyé en Dioula",
      "url": "http://localhost:8000/audio/dioula.mp3",
      "taille_mb": 2.81
    },
    {
      "id": "fulfulde",
      "langue": "fulfulde",
      "description": "Version officielle de l'hymne national Le Ditanyé en Fulfulde",
      "url": "http://localhost:8000/audio/fulfulde.mp3",
      "taille_mb": 2.41
    }
  ]
}
```

### Test 2: Question "Hymne national"

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hymne national du Burkina Faso"}'
```

**Résultat**:
```
L'Hymne National du Burkina Faso, LE DITANYÉ :

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
La Patrie ou la mort, nous vaincrons !

🎵 **Versions audio disponibles** :
- En Moore : http://localhost:8000/audio/moore.mp3
- En Dioula : http://localhost:8000/audio/dioula.mp3
- En Fulfulde : http://localhost:8000/audio/fulfulde.mp3
```

### Test 3: Accès Direct aux Fichiers Audio

```bash
# Test Moore
curl -I http://localhost:8000/audio/moore.mp3
# Résultat: HTTP/1.1 200 OK ✅

# Test Dioula
curl -I http://localhost:8000/audio/dioula.mp3
# Résultat: HTTP/1.1 200 OK ✅

# Test Fulfulde
curl -I http://localhost:8000/audio/fulfulde.mp3
# Résultat: HTTP/1.1 200 OK ✅
```

---

## 📊 Structure de `audio_index.json`

```json
{
  "moore": {
    "id": "moore",
    "path": "static/audio/moore.mp3",
    "filename": "moore.mp3",
    "size_bytes": 3502790,
    "size_mb": 3.34,
    "transcription": "Hymne national du Burkina Faso en langue Moore (Ditanyé)",
    "langue": "moore",
    "categorie": "hymne_national",
    "tonalite": "solennel",
    "description": "Version officielle de l'hymne national Le Ditanyé en Moore"
  },
  "dioula": {
    "id": "dioula",
    "path": "static/audio/dioula.mp3",
    "filename": "dioula.mp3",
    "size_bytes": 2941680,
    "size_mb": 2.81,
    "transcription": "Hymne national du Burkina Faso en langue Dioula (Faso Fasa)",
    "langue": "dioula",
    "categorie": "hymne_national",
    "tonalite": "solennel",
    "description": "Version officielle de l'hymne national Le Ditanyé en Dioula"
  },
  "fulfulde": {
    "id": "fulfulde",
    "path": "static/audio/fulfulde.mp3",
    "filename": "fulfulde.mp3",
    "size_bytes": 2524095,
    "size_mb": 2.41,
    "transcription": "Hymne national du Burkina Faso en langue Fulfulde",
    "langue": "fulfulde",
    "categorie": "hymne_national",
    "tonalite": "solennel",
    "description": "Version officielle de l'hymne national Le Ditanyé en Fulfulde"
  }
}
```

---

## 🔗 Endpoints Disponibles

### 1. `GET /hymne-audio`
Retourne la liste des versions audio de l'hymne disponibles

**Réponse**:
```json
{
  "available": true,
  "count": 3,
  "hymnes": [...]
}
```

### 2. `GET /audio/{filename}`
Accès direct aux fichiers audio MP3

**Exemples**:
- http://localhost:8000/audio/moore.mp3
- http://localhost:8000/audio/dioula.mp3
- http://localhost:8000/audio/fulfulde.mp3

### 3. `POST /ask`
Question sur l'hymne national → Retourne texte + liens audio

**Requête**:
```json
{
  "question": "Hymne national du Burkina Faso"
}
```

**Réponse**: Texte complet + 3 liens vers les versions audio

---

## 🎯 Utilisation

### Via l'API REST

```python
import requests

# 1. Lister les hymnes disponibles
response = requests.get("http://localhost:8000/hymne-audio")
hymnes = response.json()["hymnes"]

# 2. Télécharger un fichier audio
audio_url = hymnes[0]["url"]
audio_data = requests.get(audio_url).content
with open("hymne_moore.mp3", "wb") as f:
    f.write(audio_data)

# 3. Demander l'hymne via le chatbot
response = requests.post(
    "http://localhost:8000/ask",
    json={"question": "Hymne national du Burkina Faso"}
)
print(response.json()["response"])  # Texte + liens audio
```

### Via l'Interface Web

Quand un utilisateur demande l'hymne national, le chatbot affiche:
1. ✅ Le texte complet de l'hymne
2. 🎵 Les 3 liens cliquables vers les versions audio

---

## 🚀 Avantages de cette Intégration

1. **Multilingue**: 3 langues locales principales du Burkina Faso
2. **Accessible**: Fichiers audio directement accessibles via HTTP
3. **Automatique**: Liens ajoutés automatiquement à la réponse
4. **Extensible**: Facile d'ajouter de nouvelles versions audio
5. **Léger**: API GET simple pour lister les fichiers disponibles

---

## 📝 Ajouter de Nouvelles Versions Audio

### Étape 1: Ajouter le fichier MP3
```bash
cp nouvel_hymne.mp3 static/audio/
```

### Étape 2: Mettre à jour `audio_index.json`
```json
{
  "nouvelle_langue": {
    "id": "nouvelle_langue",
    "path": "static/audio/nouvel_hymne.mp3",
    "filename": "nouvel_hymne.mp3",
    "size_bytes": 0,
    "size_mb": 0,
    "transcription": "Hymne national en nouvelle langue",
    "langue": "nouvelle_langue",
    "categorie": "hymne_national",
    "tonalite": "solennel",
    "description": "Description de la nouvelle version"
  }
}
```

### Étape 3: Redémarrer le serveur
```bash
# Le serveur recharge automatiquement l'index au démarrage
```

Ou utiliser le script automatique:
```bash
python create_audio_index.py
```

---

## 🔍 Logs de Validation

Au démarrage du serveur, vous devriez voir:
```
✅ Index audio chargé: 3 fichiers audio disponibles
```

Cela confirme que les 3 versions audio de l'hymne sont bien chargées et prêtes à être servies.

---

## 📚 Documentation Connexe

- **CORRECTIFS_APPLIQUES.md** → Correctifs des réponses bizarres
- **GUIDE_CONFIGURATION.md** → Configuration des modèles et voix
- **VOICE_FEATURES.md** → Fonctionnalités vocales complètes

---

**Statut Final**: ✅ Intégration audio complète et opérationnelle

Les utilisateurs peuvent maintenant:
- ✅ Demander l'hymne national et obtenir le texte + liens audio
- ✅ Accéder directement aux fichiers MP3 via les URLs
- ✅ Lister programmatiquement les versions disponibles via `/hymne-audio`
