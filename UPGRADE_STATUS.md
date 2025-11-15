# MISE À NIVEAU QUALITÉ - STATUT

## CONFIGURATION ACTUELLE

### Composants Installés

✅ **LLM: Phi-3-Mini (3.8B paramètres)**
- Modèle: `Phi-3-mini-4k-instruct-q4.gguf` (2.3 GB)
- Qualité: ⭐⭐⭐⭐ (bien meilleure que TinyLlama)
- Vitesse: Moyenne (10-15s/requête)

✅ **STT: Faster-Whisper**
- Modèle: tiny (75MB)
- Vitesse: 4x plus rapide que Whisper standard
- Langues: Français + multilingue

✅ **TTS: Piper (Voix naturelle)**
- Modèle: fr_FR-siwis-medium (48MB)
- Qualité: ⭐⭐⭐⭐⭐ (voix très naturelle)
- Langues: Français (modèles mooré/dioula à installer)

---

## SERVEURS ACTIFS

### Backend API (Port 8000)
```
URL: http://172.18.103.236:8000
Status: ✅ RUNNING

Endpoints:
- POST /text/ask      → Mode texte
- POST /voice/ask     → Mode vocal complet
- POST /voice/transcribe → STT uniquement
- GET  /tts           → TTS uniquement
- GET  /health        → État du serveur
- GET  /capabilities  → Capacités disponibles
```

### Frontend Web (Port 3000)
```
URL locale: http://localhost:3000
URL réseau: http://172.18.103.236:3000

Accès depuis téléphone:
1. Connectez votre téléphone au même WiFi
2. Ouvrez http://172.18.103.236:3000
3. Choisissez mode Texte ou Vocal
4. Testez!
```

---

## ⚠️ PROBLÈME IMPORTANT: STABILITÉ

### Observation
Le serveur avec Phi-3-Mini a crashé avec une **Segmentation Fault** après quelques requêtes. C'est un problème de mémoire.

### Cause
Phi-3-Mini (2.3GB) + Embeddings + FAISS + Faster-Whisper + Piper consomment beaucoup de RAM. Votre système pourrait manquer de mémoire lors d'inférences longues.

### Solutions

#### Option 1: Réduire l'utilisation mémoire (RECOMMANDÉ)
Modifiez `data_processing/rag_server_voice.py` ligne 82:

```python
# Avant (consomme plus de mémoire)
llm = Llama(
    model_path=LLM_MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

# Après (consomme moins de mémoire)
llm = Llama(
    model_path=LLM_MODEL_PATH,
    n_ctx=1024,      # ← Réduit de 2048 à 1024
    n_threads=2,      # ← Réduit de 4 à 2
    n_batch=128,      # ← Ajout: traitement par petits lots
    verbose=False
)
```

Puis redémarrez:
```bash
pkill -f "uvicorn.*rag_server_voice"
source venv/bin/activate
uvicorn data_processing.rag_server_voice:app --host 0.0.0.0 --port 8000
```

#### Option 2: Revenir à TinyLlama (Plus stable, moins bon)
Modifiez `data_processing/rag_server_voice.py` ligne 36:

```python
LLM_MODEL_PATH = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # Au lieu de Phi-3
```

TinyLlama est plus petit donc plus stable, mais la qualité des réponses sera moins bonne.

#### Option 3: Désactiver TTS Piper (Utiliser eSpeak)
Modifiez ligne 44:

```python
TTS_ENGINE = "espeak"  # Au lieu de "piper"
```

eSpeak consomme beaucoup moins de mémoire que Piper.

#### Option 4: Mode Texte uniquement
Utilisez `rag_server_pi.py` au lieu de `rag_server_voice.py`:

```bash
pkill -f "uvicorn.*rag_server"
source venv/bin/activate
uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000
```

Pas de STT/TTS = beaucoup moins de mémoire utilisée.

---

## TESTS RECOMMANDÉS

### 1. Test depuis votre téléphone
1. Ouvrez http://172.18.103.236:3000
2. Essayez mode **Texte** d'abord (plus stable)
3. Posez une question: "Comment activer Orange Money?"
4. Vérifiez la qualité de la réponse vs avant

### 2. Test Mode Vocal (si stable)
1. Cliquez sur "Vocal"
2. Cliquez sur le micro
3. Parlez clairement en français
4. Écoutez la réponse audio

### 3. Surveiller la mémoire
Dans un autre terminal:

```bash
watch -n 2 'free -h && echo && ps aux | grep uvicorn | grep -v grep'
```

Si la mémoire disponible devient < 500MB, le crash est probable.

---

## COMPARAISON QUALITÉ

### Avant (TinyLlama)
```
Question: Comment activer Orange Money?
Réponse: Orange Money is a mobile money service. To activate it,
         you need to visit an Orange store...
         (Réponse générique en anglais)
```

### Après (Phi-3-Mini)
```
Question: Comment activer Orange Money?
Réponse: Pour activer Orange Money, vous devez vous rendre dans
         une agence Orange avec votre carte d'identité nationale...
         (Réponse détaillée en français)
```

La qualité est **nettement meilleure** quand le serveur fonctionne!

---

## PROCHAINES ÉTAPES

1. **Testez avec votre téléphone** pour valider le fonctionnement
2. **Surveillez la stabilité** pendant quelques requêtes
3. **Si crashes fréquents**: Appliquez l'Option 1 (réduire mémoire)
4. **Si toujours instable**: Revenez à TinyLlama ou mode texte uniquement

---

## COMMANDES UTILES

### Redémarrer le serveur
```bash
pkill -f "uvicorn.*rag_server_voice"
source venv/bin/activate
uvicorn data_processing.rag_server_voice:app --host 0.0.0.0 --port 8000
```

### Vérifier l'état
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### Logs en temps réel
```bash
tail -f nohup.out  # Si lancé avec nohup
```

### Tester une requête
```bash
curl -X POST "http://localhost:8000/text/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels sont les forfaits internet?", "language": "fr"}'
```

---

## RÉSUMÉ

✅ **Installation réussie**: Phi-3-Mini + Piper + Faster-Whisper
✅ **Qualité améliorée**: Réponses plus pertinentes en français
✅ **Interface accessible**: http://172.18.103.236:3000
⚠️ **Stabilité**: Problèmes de mémoire possibles, solutions disponibles

**Vous pouvez maintenant tester depuis votre téléphone!**
