# TABLEAU COMPARATIF DES 6 SERVEURS RAG

| Critère | gpt4all (ACTIF) | voice | openai | claude | pi | tts |
|---------|-----------------|-------|--------|--------|-----|-----|
| **LLM Provider** | Groq API | Groq API | OpenAI | Anthropic | Llama-CPP | Llama-CPP |
| **LLM Model** | llama-3.1-8b-instant | llama-3.1-8b-instant | gpt-4o-mini | haiku-20241022 | tinyllama-1.1b | tinyllama-1.1b |
| **Model Type** | Cloud API | Cloud API | Cloud API | Cloud API | Local GGUF | Local GGUF |
| **Coût** | Gratuit/Free | Gratuit/Free | Payant | Payant | Gratuit | Gratuit |
| | | | | | | |
| **STT Support** | Groq Whisper | Whisper/Vosk/Faster-Whisper | Non | Non | Non | Non |
| **TTS Support** | Edge-TTS | Piper/espeak | Non | Non | Non | Piper/espeak |
| **Voice Full Stack** | Oui | Oui (STT+RAG+TTS) | Non | Non | Non | Non |
| | | | | | | |
| **FAISS Index** | orange_faq.index (v1) | orange_faq_v2.index (v2) | orange_faq.index | orange_faq.index | orange_faq.index | orange_faq.index |
| **TOP_K Passages** | 5 | 3 | 5 | 5 | 3 | 3 |
| | | | | | | |
| **Endpoints** | 6 major | 13 major | 2 | 2 | 1 | ? |
| **Multilingue** | Basic | fr/moore/dioula/fulfulde | Non | Non | Non | Non |
| **Audio Cache** | Static files | + TTS cache | Non | Non | Non | Oui |
| | | | | | | |
| **Optimisation** | Web/API | Raspberry Pi 5 | - | - | Pi 5 CPU | Pi 5 |
| **RAM Usage** | - | Dynamic | - | - | 800MB-2.3GB | 800MB-2.3GB |
| **Latency** | Faible | Faible | Moyen | Moyen | Variable | Variable |
| | | | | | | |
| **Local Knowledge** | Oui (hardcoded) | Oui (JSON/dict) | Non | Non | Non | Non |
| **CORS Enabled** | Oui | Oui | Non | Non | Non | Non |
| | | | | | | |
| **Code Quality** | Mature (504L) | Très mature (981L) | Simple (87L) | Simple (84L) | Basique (100L) | Moyen (250L) |
| **Documentation** | Incluse | Complète | Incluse | Incluse | Incluse | Incluse |
| | | | | | | |
| **Production Ready** | OUI | OUI | OUI | OUI | LIMITE | NON |
| **Status** | ACTIVE | ADVANCED | SECONDARY | SECONDARY | EXPERIMENTAL | EXPERIMENTAL |

---

# MATRICE DE DÉCISION: Quel Serveur Utiliser?

## Cas d'Utilisation

### 1. **Production Web Standard**
- Utiliser: `rag_server_gpt4all.py`
- Raison: Groq gratuit, Edge-TTS gratuit, endpoints complets
- Déploiement: Cloud, VPS, Docker
- Coût: Gratuit (API Groq)

### 2. **Interface Vocale Complète (STT+RAG+TTS)**
- Utiliser: `rag_server_voice.py`
- Raison: Support multilingue, cache TTS, stats système
- Déploiement: Raspberry Pi 5, serveur puissant
- Coût: Gratuit

### 3. **Déploiement Raspberry Pi 5 (Basique)**
- Utiliser: `rag_server_pi.py`
- Raison: Optimisé ressources, local LLM, no internet needed
- Coût: Gratuit
- NOTE: Qualité inférieure à Groq

### 4. **Intégration OpenAI Existante**
- Utiliser: `rag_server_openai.py`
- Raison: Minimal, simple, compatible
- Coût: Payant (OpenAI API)
- NOTE: Pas de voice

### 5. **Intégration Anthropic Existante**
- Utiliser: `rag_server_claude.py`
- Raison: Minimal, simple, compatible
- Coût: Payant (Anthropic API)
- NOTE: Pas de voice

### 6. **Prototype / Test Local LLM**
- Utiliser: `rag_server_tts.py`
- Raison: Expérimental, TTS intégré
- Coût: Gratuit
- NOTE: Qualité variable

---

# FICHIERS CRITIQUES À CHANGER

## Pour Migration gpt4all → voice
1. INDEX: `orange_faq.index` → `orange_faq_v2.index`
2. METADATA: `metadata.json` → `metadata_v2.json`
3. SERVEUR: Importer de data_processing.rag_server_voice
4. TEST: `/voice/ask` endpoint

## Pour Migration gpt4all → pi
1. MODEL PATH: Définir à `Phi-3-mini` ou `Llama-3.2`
2. CONFIGURATION: Ajuster n_threads, n_ctx pour Pi
3. INDEXATION: Utiliser FAISS local
4. DÉPLOIEMENT: Sur Raspberry Pi 5

---

# SÉCURITÉ: Checklist

### Problèmes Identifiés
- [x] .env contient clés API en clair
- [x] index_data.py a credentials hardcodées
- [x] .gitignore ne protège pas tous les fichiers secrets
- [x] GROQ_API_KEY valide et active (risque d'abus)

### Actions Recommandées
1. Rotate GROQ_API_KEY (immédiat)
2. Rotate OpenAI/Google keys
3. Utiliser secrets manager (Docker, K8s, Vault)
4. Nettoyer .env du repo
5. Add pre-commit hooks pour détection secrets

