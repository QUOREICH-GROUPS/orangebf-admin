# Déploiement complet sur Raspberry Pi 5 (CanaKit 8 Go)

## Prérequis matériels

- Raspberry Pi 5 8 Go (CanaKit Pro) avec carte micro‑SD 128 Go.
- OS : Raspberry Pi OS 64 bits (Bookworm).
- Réseau local accessible depuis votre machine (SSH).

## Installation de base

1. Mettre à jour :
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Installer dépendances :
   ```bash
   sudo apt install -y python3.11 python3.11-venv git nginx postgresql
   ```
3. Cloner ou copier le projet vers `/home/pi/orangebf`.

## Backend FastAPI

```bash
cd /home/pi/orangebf
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configurer `.env` (GROQ_API_KEY, EDGE_TTS keys, DATABASE_URL, etc.).

### Service systemd

Créer `/etc/systemd/system/orange.service` :

```
[Unit]
Description=Orange RAG API
After=network.target postgresql.service

[Service]
User=pi
WorkingDirectory=/home/pi/orangebf
Environment=\"PYTHONUNBUFFERED=1\"
ExecStart=/home/pi/orangebf/venv/bin/uvicorn data_processing.rag_server_voice:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Puis :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now orange.service
```

## PostgreSQL (logging Q/A)

```bash
sudo -u postgres createuser orange --pwprompt
sudo -u postgres createdb -O orange orange_chat
psql -U orange orange_chat < scripts/chat_logs.sql
```

Assurez-vous que `DATABASE_URL` pointe vers cette base.

## Frontend (PWA)

1. Sur votre machine :
   ```bash
   cd admin-robot-ui
   npm install
   npm run build
   ```
2. Copier `dist/` sur la Pi (`/home/pi/orangebf/ui/dist`).

3. Configurer Nginx (`/etc/nginx/sites-available/orange`):

```
server {
    listen 80;
    server_name _; # ou pi5.orange.local

    location / {
        root /home/pi/orangebf/ui/dist;
        try_files $uri /index.html;
    }

    location /sw.js {
        add_header Cache-Control \"no-cache\";
        root /home/pi/orangebf/ui/dist;
    }

    location /manifest.webmanifest {
        root /home/pi/orangebf/ui/dist;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }
}
```

Enable + reload :

```bash
sudo ln -s /etc/nginx/sites-available/orange /etc/nginx/sites-enabled/orange
sudo nginx -t
sudo systemctl restart nginx
```

## Pipeline de déploiement

Un script `deploy.sh` est fourni :

```bash
./deploy.sh pi@pi5.local /home/pi/orangebf
```

Il enchaîne :
1. `npm run build` dans `admin-robot-ui`.
2. `rsync` du dépôt (hors `.git`, `venv`, `node_modules`) vers la Pi.
3. `rsync` de `dist/` vers `ui/dist`.
4. `ssh` pour `sudo systemctl restart orange.service`.

## Vérifications finales

- Accéder à `http://pi5.orange.local` → l’app se charge, propose “Ajouter à l’écran d’accueil”.
- Live Chat (texte + voix) fonctionne et loggue dans Postgres.
- `sudo systemctl status orange.service` : doit afficher “active (running)”.
- `journalctl -u orange.service` pour inspecter les logs backend.

Ce pipeline permet de pousser des mises à jour complètes en une commande tout en respectant les contraintes du Pi 5.
