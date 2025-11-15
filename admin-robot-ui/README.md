# Admin Robot UI

Interface d'administration React + TypeScript permettant de piloter le backend `rag_server_voice.py` (RAG + TTS + Audio) depuis une console moderne.

## Démarrage rapide

```bash
cd admin-robot-ui
npm install
# API FastAPI accessible sur http://localhost:8000 par défaut
npm run dev
```

- Définir `VITE_API_URL` si le backend est sur une autre adresse/port :

```bash
VITE_API_URL="http://192.168.1.50:8000" npm run dev
```

## Structure

```
admin-robot-ui/
├── public/index.html        # Point d'entrée statique
├── src/index.tsx            # Bootstrap React
├── src/App.tsx              # Layout principal (Navbar + Sidebar + vues)
├── src/styles/main.css      # Thème Orange Faso
├── src/components/          # Composants métiers
│   ├── Navbar.tsx           # En-tête + statut live
│   ├── Sidebar.tsx          # Navigation latérale
│   ├── FAQManager.tsx       # Gestion FAISS (import, segments, purge)
│   ├── VoiceTester.tsx      # Test RAG + TTS
│   ├── UserGreetings.tsx    # Uploads audio + salutations
│   ├── Settings.tsx         # Paramètres LLM/TTS/Réseau
│   └── ChatHistory.tsx      # Journal & métriques
├── src/services/
│   ├── api.js               # Appels REST généralistes
│   └── faissService.js      # Opérations dédiées à l'index FAISS
├── package.json             # Scripts npm (Vite, TypeScript)
└── vite.config.ts           # Configuration locale
```

## Fonctionnalités clés

- **Navbar + Sidebar** : navigation instantanée entre modules + filtres (catégorie, langue, utilisateur).
- **FAQManager** : upload/modif/suppression de documents, annotations locales, recherche instantanée et test de pertinence FAISS.
- **VoiceTester** : choix langue/voix Edge-TTS, génération audio, commandes Play/Stop/Save.
- **Live Conversation** : simule un chat type ChatGPT/Gemini (mode RAG ou LLM Libre), responsive, plein écran, texte + voix, lecture auto TTS.
- **Audios & Salutations** : dépôt d'hymnes/salutations, filtre par langue, planification locale de messages contextuels + préécoute TTS (Play/Stop/Enregistrer comme dans l’onglet Voix).
- **Paramètres** : formulaires dialogue/voix/réseau. Si `/settings/*` n'est pas exposé, les valeurs sont sauvegardées localement (via `/capabilities`/`/health`) puis poussées dès que `rag_server_voice.py` est disponible.
- **Journal** : filtre par module + plage de dates, respect du filtre utilisateur global (catégorie/utilisateur/langue).
- **PWA** : manifest + service worker intégrés pour installer l’interface sur mobile/desktop et bénéficier d’un cache offline.

## Build & déploiement (Pi 5)

```bash
npm run build
# Copiez ensuite dist/ vers votre PI 5 et servez-le en statique (nginx, Caddy, uvicorn+StaticFiles …)
```

Sur Raspberry Pi 5 :

1. Installez `nodejs`/`npm` récents (ou construisez le bundle sur une machine x86 et copiez `dist/`).
2. Exposez le backend FastAPI avec `uvicorn data_processing.rag_server_voice:app --host 0.0.0.0 --port 8000`.
3. Servez `dist/` (par exemple `python3 -m http.server` derrière un reverse proxy) et pointez `VITE_API_URL` vers `http://<ip_pi>:8000`. Utilisez `TSC_COMPILE_ON_SAVE=false`/`npm run build` pour réduire la charge CPU pendant la compilation sur le Pi.
