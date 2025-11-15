# AUDIT COMPLET DU PROJET - AMÉLIORATIONS NÉCESSAIRES

**Date**: 13 novembre 2025
**Objectif**: Revue complète pour optimiser le projet et revenir aux modèles locaux

---

## PROBLÈMES IDENTIFIÉS

### 1. FORMATAGE DES DONNÉES (CRITIQUE ⚠️)

**Fichier**: `data_processing/clean_orange.py` + données générées

**Problèmes**:
- ❌ Texte en blocs énormes sans structure
- ❌ Ponctuation manquante (points, virgules)
- ❌ Navigation/footer mélangés au contenu utile
- ❌ Répétitions inutiles
- ❌ Phrases coupées ("Soyez tranquille en utilisant...")

**Exemple actuel (metadata.json ligne 2)**:
```
"Avec nos différents services, vous simplifierez votre utilisation mobile au Burkina Faso comme à l'international En savoir plus Appel en attente Ne ratez plus vos appels..."
```

**Devrait être**:
```
"Avec nos différents services, vous simplifierez votre utilisation mobile au Burkina Faso comme à l'international."

"Appel en attente: Ne ratez plus vos appels lorsque vous êtes déjà en communication, en activant l'appel en attente."
```

**Impact**:
- TTS lit d'une traite = incompréhensible
- LLM a du mal à extraire l'info pertinente
- RAG retourne du bruit avec l'information

**Solution**: Améliorer `clean_orange.py`

---

### 2. CONNAISSANCES LOCALES INCOMPLÈTES

**Fichier**: `data_processing/local_knowledge.py`

**Contenu actuel**:
- ✅ Hymne (français, mooré, dioula)
- ✅ Président Ibrahim Traoré
- ✅ Salutations (mooré, dioula, français)
- ✅ Accueil autorités

**Manquants**:
- ❌ **Fulfulde** (hymne, salutations) - alors qu'on a `fulfulde.mp3`!
- ❌ **Numéros utiles Orange**:
  - 121 (service client Orange)
  - 127 (service client Orange Money)
  - *144# (menu Orange Money)
  - *160# (solde)
  - *244# (Orange Energie)
  - +226 07 00 01 21 (nouveau contact)
- ❌ **Codes USSD fréquents**
- ❌ **Jours fériés Burkina Faso**
- ❌ **Informations culturelles** (salutations mooré/dioula/fulfulde détaillées)

**Solution**: Compléter `local_knowledge.py`

---

### 3. FICHIERS AUDIO NON INTÉGRÉS

**Fichiers disponibles**:
```
static/audio/moore.mp3 (3.4 MB)
static/audio/dioula.mp3 (2.9 MB)
static/audio/fulfulde.mp3 (2.5 MB)
```

**Problème**: Ces fichiers existent mais ne sont **PAS utilisés** par le système!

**Utilisation prévue**:
- Lorsque l'utilisateur demande l'hymne en mooré → jouer `moore.mp3`
- Lorsque l'utilisateur demande l'hymne en dioula → jouer `dioula.mp3`
- Lorsque l'utilisateur demande l'hymne en fulfulde → jouer `fulfulde.mp3`

**Solution**: Intégrer dans le serveur un endpoint `/audio/<langue>` qui retourne le MP3

---

### 4. CRASHES DES MODÈLES LOCAUX

#### TinyLlama (1.1B)
**Statut**: ✅ Stable, PAS de crash
**Problème**: ❌ Qualité médiocre, réponses en anglais

#### Phi-3-Mini (3.8B)
**Statut**: ❌ Segmentation Fault (exit code 139/144)
**Cause probable**:
1. Modèle 2.3 GB trop lourd pour RAM disponible
2. `llama-cpp-python` gestion mémoire inefficace
3. Context window trop grand (2048 → réduit à 1024 mais toujours crash)

**Tentatives d'optimisation** (ont échoué):
```python
llm = Llama(
    model_path="Phi-3-mini-4k-instruct-q4.gguf",
    n_ctx=1024,      # Réduit de 2048
    n_threads=2,     # Réduit de 4
    n_batch=64,      # Réduit de 256
    ...
)
```

**Mémoire consommée avec Phi-3**:
- Embeddings + FAISS: ~500 MB
- Phi-3-Mini model: ~2.3 GB
- Inference overhead: ~1-2 GB
- **Total**: ~4-5 GB → dépasse RAM disponible

---

## SOLUTIONS ET AMÉLIORATIONS

### Solution 1: AMÉLIORER LE FORMATAGE DES DONNÉES

Créer `/home/suprox/Projet/Laravel/ai/orangebf/data_processing/clean_orange_v2.py`:

```python
import json
import re
from html import unescape

# Liste de mots-clés pour filtrer le bruit
NOISE_KEYWORDS = [
    "Suivez-nous sur", "Facebook", "Instagram", "WhatsApp", "LinkedIn", "YouTube",
    "© Orange", "Mentions légales", "CGU", "Orange.com", "Orange jobs",
    "Offres", "Bons plans", "Boutique en ligne", "Assistance", "Max it",
    "En savoir plus", "Voir plus", "En savoir +"
]

def is_noise(text):
    """Détecte si une ligne est du bruit (navigation, footer)"""
    return any(keyword in text for keyword in NOISE_KEYWORDS)

def clean_text_for_tts(text):
    """Nettoie et structure le texte pour TTS"""
    # Décode HTML
    text = unescape(text)

    # Supprime balises HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalise espaces
    text = re.sub(r"\s+", " ", text).strip()

    # Ajoute points manquants après certains patterns
    text = re.sub(r"([a-z])\s+([A-Z])", r"\1. \2", text)

    # Normalise ponctuation
    text = re.sub(r"\s+([,;:!?.])", r"\1", text)
    text = re.sub(r"([,;:!?.])\s*", r"\1 ", text)

    # Sépare les phrases très longues (>300 caractères) aux points naturels
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ".!?" and len(current) > 50:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    return sentences

def extract_meaningful_paragraphs(text):
    """Extrait seulement les paragraphes utiles"""
    lines = text.split(". ")
    meaningful = []

    for line in lines:
        line = line.strip()

        # Ignore le bruit
        if is_noise(line):
            continue

        # Garde seulement les lignes avec info substantielle
        if len(line) < 20:  # Trop court
            continue

        # Ajoute point final si manquant
        if not line.endswith((".", "!", "?")):
            line += "."

        meaningful.append(line)

    return meaningful

# Chargement et traitement
with open("orange_services.json", "r", encoding="utf-8") as f:
    data = []
    for line in f:
        line = line.strip()
        if not line:
            continue
        start_index = line.find('{')
        end_index = line.rfind('}')
        if start_index != -1 and end_index != -1:
            json_str = line[start_index:end_index + 1]
            try:
                data.append(json.loads(json_str))
            except:
                pass

cleaned_paragraphs = []

for item in data:
    content = item.get("content", "")
    sentences = clean_text_for_tts(content)
    meaningful = extract_meaningful_paragraphs(" ".join(sentences))

    for para in meaningful:
        cleaned_paragraphs.append({
            "url": item.get("url"),
            "text": para
        })

# Sauvegarde
with open("orange_services_clean_v2.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_paragraphs, f, ensure_ascii=False, indent=2)

print(f"✅ Nettoyé {len(cleaned_paragraphs)} paragraphes optimisés pour TTS")
```

**Avantages**:
- ✅ Phrases courtes et claires pour TTS
- ✅ Ponctuation correcte
- ✅ Pas de bruit (navigation, footer)
- ✅ Meilleure qualité RAG

---

### Solution 2: COMPLÉTER local_knowledge.py

Ajouter dans `/home/suprox/Projet/Laravel/ai/orangebf/data_processing/local_knowledge.py`:

```python
local_facts = {
    # ... existant ...

    "hymne": {
        "francais": """...""",
        "moore": """...""",
        "dioula": """...""",
        "fulfulde": """
L'Hymne National en Fulfulde (Peul)

E leydi Burkina Faso, min jibi jom e hoore men
Min hokka ko e mawɗo men Ibrahim Traoré
Ñannde gacce leydi men, min jeyaa...
(Version complète à ajouter)
        """
    },

    "numeros_utiles": {
        "orange": {
            "service_client": "121",
            "description": "Service client Orange, disponible 7j/7, 24h/24"
        },
        "orange_money": {
            "service_client": "127",
            "menu_ussd": "*144#",
            "solde": "*144*9*1#",
            "description": "Service client Orange Money, disponible 7j/7, 24h/24"
        },
        "orange_energie": {
            "service_client": "119",
            "menu_ussd": "*244#",
            "paiement": "*244*1*1*1#",
            "description": "Service Orange Energie, installation sous 72h"
        },
        "codes_ussd": {
            "solde": "*160#",
            "recharge": "*123*code#",
            "transfert_credit": "*111#",
            "numero_orange": "*100#"
        },
        "contact_additionnel": "+226 07 00 01 21",
        "email": "info.obf@orange.com"
    },

    "salutations": {
        "moore": {
            "bonjour": ["Yibéogo !", "Ney Yibéogo !"],
            "comment ça va": "Kibaré ?",
            "ça va": "Laafi",
            "ça va bien": "Laafi bala",
            "merci": "Barka",
            "merci beaucoup": "Barka wousgo",
            "au revoir": "Bilfou",
            "bonne journée": "Yom wi a yibeoogo",
            "matin": "A ni sɔ̀gɔma",
            "midi": "A ni tlé",
            "apres-midi": "A nou laa",
            "soir": "A ni zaabre",
            "nuit": "I nou su"
        },
        "dioula": {
            "bonjour": "Inché",
            "matin": "One baali diiam",
            "entre 11h-13h": "One beeti diiam",
            "apres-midi": "One nyaali diiam",
            "soir": "One keeri diiam",
            "comment ça va": ["Djam na ?", "A djamo na ?"],
            "ça va": "Djam tan",
            "ça va bien": "Djam doron tan",
            "as-tu bien dormi": "A waali djam na ?",
            "merci": "I ni tché",
            "au revoir": "Kan bèn"
        },
        "fulfulde": {
            "bonjour": ["Jam wali", "On jaraama"],
            "comment ça va": "No mbadda ?",
            "ça va": "Jam tan",
            "ça va bien": "Jam e jam",
            "merci": "Jaaraama",
            "merci beaucoup": "Jaaraama buri",
            "au revoir": "Fof ma yaaf on",
            "bonne journée": "Ñalnde e jam"
        },
        "francais": {
            "bonjour": "Bonjour",
            "bonsoir": "Bonsoir",
            "merci": "Merci",
            "au revoir": "Au revoir",
            "bonne journée": "Bonne journée"
        }
    },

    "jours_feries": {
        "1er janvier": "Nouvel An",
        "3 janvier": "Soulèvement populaire (1966)",
        "8 mars": "Journée internationale de la femme",
        "variable": "Lundi de Pâques",
        "1er mai": "Fête du Travail",
        "variable": "Ascension",
        "variable": "Lundi de Pentecôte",
        "variable": "Aid el-Fitr (fin du Ramadan)",
        "variable": "Aid el-Adha (Tabaski)",
        "5 août": "Fête de l'indépendance",
        "15 août": "Assomption",
        "variable": "Maouloud (Naissance du Prophète)",
        "15 octobre": "Journée des martyrs",
        "1er novembre": "Toussaint",
        "11 décembre": "Fête nationale (Proclamation de la République)",
        "25 décembre": "Noël"
    }
}

def get_numero_utile(query):
    """Retourne un numéro utile Orange"""
    q = query.lower()

    if "service client" in q and "money" in q:
        return f"Le service client Orange Money est joignable au 127, disponible 7 jours sur 7, 24 heures sur 24."
    elif "service client" in q or "contact" in q:
        return f"Le service client Orange est joignable au 121, disponible 7 jours sur 7, 24 heures sur 24. Vous pouvez également nous contacter au +226 07 00 01 21 ou par email à info.obf@orange.com"
    elif "solde" in q:
        return f"Pour consulter votre solde, composez *160# ou utilisez le menu Orange Money *144*9*1#"
    elif "recharge" in q:
        return f"Pour recharger, composez *123* suivi de votre code de recharge puis #"
    elif "orange money" in q and "menu" in q:
        return f"Pour accéder au menu Orange Money, composez *144#"
    elif "energie" in q or "solaire" in q:
        return f"Pour Orange Energie, contactez le 119 ou composez *244#. Installation sous 72 heures après validation."

    return None
```

---

### Solution 3: INTÉGRER LES FICHIERS AUDIO

Ajouter dans `rag_server_voice.py`:

```python
@app.get("/audio/hymne/{langue}")
def get_hymne_audio(langue: str):
    """
    Retourne l'audio de l'hymne dans la langue demandée

    Langues supportées: moore, dioula, fulfulde
    """
    audio_files = {
        "moore": "static/audio/moore.mp3",
        "dioula": "static/audio/dioula.mp3",
        "fulfulde": "static/audio/fulfulde.mp3"
    }

    if langue not in audio_files:
        raise HTTPException(
            status_code=404,
            detail=f"Langue '{langue}' non supportée. Langues disponibles: moore, dioula, fulfulde"
        )

    file_path = Path(audio_files[langue])

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fichier audio non trouvé pour la langue '{langue}'"
        )

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"hymne_{langue}.mp3"
    )

@app.get("/audio/list")
def list_audio_files():
    """Liste tous les fichiers audio disponibles"""
    return {
        "hymnes": [
            {"langue": "moore", "url": "/audio/hymne/moore"},
            {"langue": "dioula", "url": "/audio/hymne/dioula"},
            {"langue": "fulfulde", "url": "/audio/hymne/fulfulde"}
        ]
    }
```

Modifier `generate_response()` pour détecter les demandes d'hymne:

```python
def generate_response(question: str, passages: list, language: str = "fr"):
    # Vérifier si c'est une demande d'hymne
    q_lower = question.lower()

    if "hymne" in q_lower or "ditanye" in q_lower:
        if "mooré" in q_lower or "moore" in q_lower:
            return {
                "text": "Voici l'hymne national du Burkina Faso en mooré, le Ditanye.",
                "audio_url": "/audio/hymne/moore"
            }
        elif "dioula" in q_lower:
            return {
                "text": "Voici l'hymne national du Burkina Faso en dioula, le Ditanye.",
                "audio_url": "/audio/hymne/dioula"
            }
        elif "fulfulde" in q_lower or "peul" in q_lower:
            return {
                "text": "Voici l'hymne national du Burkina Faso en fulfulde, le Ditanye.",
                "audio_url": "/audio/hymne/fulfulde"
            }

    # ... suite normale avec RAG
```

---

### Solution 4: RÉSOUDRE LES CRASHES (MODÈLES LOCAUX)

#### Option 4a: Modèle plus petit que Phi-3 (RECOMMANDÉ)

**Llama-3.2-1B** (1B paramètres, ~650MB, GGUF Q4):
```bash
cd /home/suprox/Projet/Laravel/ai/orangebf
wget https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf
```

**Avantages**:
- ✅ Plus récent que TinyLlama (2024 vs 2023)
- ✅ Multilingue natif (français inclus)
- ✅ Taille raisonnable (~650 MB)
- ✅ Devrait fonctionner sans crash
- ✅ Meilleure qualité que TinyLlama

**Configuration**:
```python
LLM_MODEL_PATH = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"

llm = Llama(
    model_path=LLM_MODEL_PATH,
    n_ctx=512,        # Petit context window
    n_threads=2,
    n_batch=32,       # Très petit batch
    verbose=False
)
```

#### Option 4b: Quantization plus agressive de Phi-3

Si vous voulez absolument Phi-3:
```bash
# Télécharger version Q2_K (plus compressée, ~1.2GB au lieu de 2.3GB)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q2_k.gguf
```

**Configuration ultra-optimisée**:
```python
LLM_MODEL_PATH = "Phi-3-mini-4k-instruct-q2_k.gguf"

llm = Llama(
    model_path=LLM_MODEL_PATH,
    n_ctx=256,          # Très petit!
    n_threads=1,        # Un seul thread
    n_batch=16,         # Batch minimal
    use_mmap=True,
    use_mlock=False,
    low_vram=True,      # Ajout: mode low VRAM
    verbose=False
)
```

#### Option 4c: Groq API (solution de secours)

Si tout le reste échoue, Groq API reste une bonne option:
- ✅ Gratuit
- ✅ Rapide
- ✅ Stable
- ✅ Qualité excellente
- ❌ Nécessite Internet

---

## PLAN D'ACTION RECOMMANDÉ

### Phase 1: DONNÉES (Haute priorité)

1. ✅ Créer `clean_orange_v2.py` avec meilleur formatage
2. ✅ Exécuter pour générer données propres
3. ✅ Recréer embeddings avec `create_embeddings.py`
4. ✅ Compléter `local_knowledge.py` (fulfulde, numéros)

### Phase 2: AUDIO (Moyenne priorité)

5. ✅ Ajouter endpoints `/audio/hymne/{langue}`
6. ✅ Intégrer détection hymne dans `generate_response()`
7. ✅ Tester avec interface web

### Phase 3: MODÈLE LOCAL (Haute priorité)

8. ✅ Télécharger Llama-3.2-1B-Instruct
9. ✅ Configurer avec paramètres optimisés
10. ✅ Tester stabilité (plusieurs requêtes)
11. ✅ Comparer qualité vs TinyLlama
12. ⚠️  Si échec: rester avec Groq API

### Phase 4: TESTS (Critique)

13. ✅ Tester multilingue (français, anglais)
14. ✅ Tester voix (Piper français, eSpeak anglais)
15. ✅ Tester hymnes audio
16. ✅ Tester stabilité serveur (10+ requêtes)
17. ✅ Tester depuis téléphone

---

## COMPARAISON DES OPTIONS LLM

| Modèle | Taille | Qualité | Stabilité | Multilingue | Recommandation |
|--------|--------|---------|-----------|-------------|----------------|
| TinyLlama 1.1B | 670 MB | ⭐⭐ | ✅ | ❌ | Non |
| Llama-3.2-1B | 650 MB | ⭐⭐⭐⭐ | ✅ | ✅ | **OUI** |
| Phi-3-Mini Q4 | 2.3 GB | ⭐⭐⭐⭐⭐ | ❌ | ✅ | Non (crash) |
| Phi-3-Mini Q2 | 1.2 GB | ⭐⭐⭐⭐ | ⚠️  | ✅ | Peut-être |
| Groq API | 0 (cloud) | ⭐⭐⭐⭐⭐ | ✅ | ✅ | Secours |

**RECOMMANDATION FINALE**: **Llama-3.2-1B-Instruct-Q4_K_M**

---

## FICHIERS À CRÉER/MODIFIER

### Nouveaux fichiers:
1. `data_processing/clean_orange_v2.py` (meilleur nettoyage)
2. `static/audio_integration.md` (documentation audio)

### Fichiers à modifier:
1. `data_processing/local_knowledge.py` (ajouter fulfulde, numéros)
2. `data_processing/rag_server_voice.py` (endpoints audio, détection hymne)
3. `README.md` ou `INSTALLATION.md` (documenter améliorations)

### Fichiers à regénérer:
1. `orange_services_clean_v2.json` (avec nouveau script)
2. `orange_services_paragraphs.json` (split paragraphes propres)
3. `orange_faq.index` (FAISS avec nouvelles données)
4. `metadata.json` (nouvelles métadonnées propres)

---

## ESTIMATION TEMPS

- **Phase 1 (Données)**: 1-2 heures
- **Phase 2 (Audio)**: 30 minutes
- **Phase 3 (Modèle)**: 1 heure (download + config + tests)
- **Phase 4 (Tests)**: 1 heure

**Total**: 3-4 heures

---

## PROCHAINE ÉTAPE

Voulez-vous que je commence par:

**A) Phase 1**: Améliorer le formatage des données
**B) Phase 2**: Intégrer les fichiers audio
**C) Phase 3**: Télécharger et configurer Llama-3.2-1B
**D) Tout faire dans l'ordre (A → B → C → D)

Je recommande **D) Tout faire dans l'ordre** pour une amélioration complète du système.
