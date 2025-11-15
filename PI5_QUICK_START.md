# 🚀 Quick Start - Raspberry Pi 5 Deployment

## TL;DR - 3 Commandes pour Démarrer

```bash
# 1. Lancer l'installation automatique
./setup_pi5.sh

# 2. Activer l'environnement virtuel
source venv/bin/activate

# 3. Démarrer le serveur
uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000
```

**C'est tout!** Votre serveur RAG est prêt à répondre aux questions.

---

## 📋 Modèles Recommandés (100% Open Source & Gratuits)

| Modèle | Taille | RAM | Vitesse | Qualité | Idéal pour |
|--------|--------|-----|---------|---------|------------|
| **Phi-3-Mini** ⭐ | 2.3 GB | ~3 GB | 5-8 tok/s | ⭐⭐⭐⭐⭐ | **Production** |
| **TinyLlama** | 0.6 GB | ~1 GB | 15-20 tok/s | ⭐⭐⭐ | Tests rapides |
| **Llama-3.2-3B** | 2.0 GB | ~2.5 GB | 6-10 tok/s | ⭐⭐⭐⭐⭐ | Balance |

**Tous sont gratuits, open-source, et fonctionnent offline!**

---

## 🎯 Installation Manuelle (Si setup_pi5.sh ne fonctionne pas)

### 1. Installer les dépendances système
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv cmake build-essential
```

### 2. Créer environnement Python
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer packages Python
```bash
pip install llama-cpp-python
pip install fastapi uvicorn pydantic sentence-transformers faiss-cpu numpy psutil
```

### 4. Télécharger un modèle

**Option A: Phi-3-Mini (RECOMMANDÉ)**
```bash
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
```

**Option B: TinyLlama (Plus rapide)**
```bash
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 5. Configurer le serveur
Éditer `data_processing/rag_server_pi.py` ligne 20:
```python
MODEL_PATH = "Phi-3-mini-4k-instruct-q4.gguf"  # Ou le nom de votre modèle
```

### 6. Lancer!
```bash
uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000
```

---

## ✅ Tests

### Test 1: Health check
```bash
curl http://localhost:8000/health
```

**Réponse attendue:**
```json
{"status": "ok", "platform": "Raspberry Pi 5", "model": "Phi-3-mini-4k-instruct-q4.gguf"}
```

### Test 2: Statistiques RAM
```bash
curl http://localhost:8000/stats
```

### Test 3: Poser une question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment activer Orange Money?"}'
```

---

## 🔧 Démarrage Automatique (Service Systemd)

### 1. Créer le fichier service
```bash
sudo nano /etc/systemd/system/orange-rag.service
```

### 2. Copier cette configuration
```ini
[Unit]
Description=Orange RAG Chatbot Server
After=network.target

[Service]
Type=simple
User=suprox
WorkingDirectory=/home/suprox/Projet/Laravel/ai/orangebf
Environment="PATH=/home/suprox/Projet/Laravel/ai/orangebf/venv/bin"
ExecStart=/home/suprox/Projet/Laravel/ai/orangebf/venv/bin/uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Activer le service
```bash
sudo systemctl daemon-reload
sudo systemctl enable orange-rag
sudo systemctl start orange-rag

# Vérifier le status
sudo systemctl status orange-rag

# Voir les logs
sudo journalctl -u orange-rag -f
```

**Le serveur démarrera automatiquement au boot du Pi!**

---

## 📊 Performances Attendues

### Avec Phi-3-Mini Q4 sur Pi 5:
- **Temps de démarrage**: 30-60 secondes
- **RAM utilisée**: ~3 GB (sur 8 GB disponibles)
- **Vitesse de génération**: 5-8 tokens/seconde
- **Temps de réponse**: 8-15 secondes par question
- **Qualité**: Excellente (comparable à GPT-3.5)

### Avec TinyLlama Q4 sur Pi 5:
- **Temps de démarrage**: 10-15 secondes
- **RAM utilisée**: ~1 GB
- **Vitesse de génération**: 15-20 tokens/seconde
- **Temps de réponse**: 3-6 secondes par question
- **Qualité**: Correcte (basique mais utilisable)

---

## 🌡️ Monitoring

### Vérifier la température
```bash
vcgencmd measure_temp
```

**⚠️ Si >70°C**: Installer un ventilateur actif

### Monitorer CPU/RAM en temps réel
```bash
htop
```

### Vérifier l'utilisation disque
```bash
df -h
```

---

## 🐛 Problèmes Courants

### Erreur: "Out of memory"
**Solution 1**: Utiliser TinyLlama au lieu de Phi-3
```bash
# Télécharger TinyLlama
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Modifier rag_server_pi.py
MODEL_PATH = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
```

**Solution 2**: Augmenter le swap
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Changer: CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Erreur: "llama-cpp-python not found"
```bash
source venv/bin/activate
pip install llama-cpp-python --force-reinstall
```

### Le serveur est trop lent
**Solutions**:
1. Réduire `max_tokens` dans `rag_server_pi.py` (ligne 70)
2. Réduire `TOP_K` à 2 (ligne 19)
3. Utiliser TinyLlama
4. Overclock le Pi (avec refroidissement!)

---

## 🌐 Accès Réseau

### Depuis votre ordinateur sur le même réseau
```bash
# Trouver l'IP du Pi
hostname -I

# Accéder depuis un autre appareil
curl http://192.168.1.X:8000/health  # Remplacer X
```

### Depuis un navigateur web
Ouvrez: `http://192.168.1.X:8000/docs` pour l'interface Swagger

---

## 💡 Conseils Pro

### 1. Garder le serveur actif avec tmux
```bash
# Démarrer une session tmux
tmux new -s rag

# Lancer le serveur
source venv/bin/activate
uvicorn data_processing.rag_server_pi:app --host 0.0.0.0 --port 8000

# Détacher: Ctrl+B puis D
# Réattacher plus tard: tmux attach -t rag
```

### 2. Logs en temps réel
```bash
# Si systemd service
sudo journalctl -u orange-rag -f

# Si tmux
tmux attach -t rag
```

### 3. Backup automatique des données
```bash
# Créer un cron job pour backup
crontab -e

# Ajouter (backup quotidien à 2h du matin)
0 2 * * * tar -czf /home/suprox/backup-$(date +\%Y\%m\%d).tar.gz /home/suprox/Projet/Laravel/ai/orangebf/*.json /home/suprox/Projet/Laravel/ai/orangebf/*.index
```

---

## 📚 Documentation Complète

- **Setup détaillé**: `RASPBERRY_PI_SETUP.md`
- **Comparaison modèles**: `SOLUTION_COMPARISON.md`
- **Architecture du projet**: `CLAUDE.md`

---

## ✨ C'est Tout!

Votre chatbot RAG Orange Burkina Faso tourne maintenant sur votre Raspberry Pi 5!

**100% Open Source | 100% Gratuit | 100% Local | 100% Offline**

Pour toute question, consultez `RASPBERRY_PI_SETUP.md` pour plus de détails.
