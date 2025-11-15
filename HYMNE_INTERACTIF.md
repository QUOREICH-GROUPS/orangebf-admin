# Hymne National Interactif - Système RAG Orange Burkina Faso

**Date**: 2025-11-14
**Statut**: ✅ Opérationnel

---

## 🎯 Vue d'Ensemble

Le système détecte automatiquement la langue demandée pour l'hymne national et retourne directement l'audio pré-enregistré avec le texte, au lieu de simples liens.

---

## 🎵 Fonctionnement

### 1. Sans Langue Spécifiée

**Question**: "Hymne national du Burkina Faso"

**Réponse**:
```
L'Hymne National du Burkina Faso, LE DITANYÉ :
[Texte complet de l'hymne...]

🎵 Versions audio disponibles :
Veuillez préciser la langue souhaitée :
- En Moore : dites 'hymne en moore'
- En Dioula : dites 'hymne en dioula'
- En Fulfulde : dites 'hymne en fulfulde'
```

### 2. Avec Langue Spécifiée

**Question**: "Hymne national en moore" ou "Hymne en dioula"

**Réponse API (`/ask`)**:
```json
{
  "question": "Hymne national en moore",
  "response": "L'Hymne National... [texte complet]\n\n🎵 Version audio en Moore :\n▶️ AUDIO: http://localhost:8000/audio/moore.mp3",
  "audio_url": "http://localhost:8000/audio/moore.mp3",
  "audio_langue": "moore"
}
```

**Réponse Interface Web (`/text/ask` avec `enable_voice: true`)**:
```json
{
  "type": "text",
  "text": "L'Hymne National... [texte complet]",
  "response": "...",
  "tts_url": "/audio/moore.mp3"  ← Audio pré-enregistré utilisé directement
}
```

---

## 🔍 Détection de Langue

Le système reconnaît les mots-clés suivants:

| Langue | Mots-clés détectés |
|--------|-------------------|
| **Moore** | moore, mooré, moré |
| **Dioula** | dioula, jula |
| **Fulfulde** | fulfulde, peul, fula |
| **Français** | français, francais, french |

### Exemples de Questions Valides

```
✅ "Hymne national en moore"
✅ "Chante-moi l'hymne en dioula"
✅ "Je veux entendre le ditanyé en fulfulde"
✅ "Hymne du Burkina en mooré"
✅ "Chanson nationale en peul"
```

---

## 🎨 Modifications Apportées

### 1. Fonction `check_local_knowledge()` (lignes 190-228)

**Nouvelle Logique**:
```python
# Hymne national
if any(word in question_lower for word in ["hymne", "ditanyé", "ditanye", "chante", "chanson nationale"]):
    # Détecter la langue demandée
    langue_detectee = None

    if any(word in question_lower for word in ["moore", "mooré", "moré"]):
        langue_detectee = "moore"
    elif any(word in question_lower for word in ["dioula", "jula"]):
        langue_detectee = "dioula"
    elif any(word in question_lower for word in ["fulfulde", "peul", "fula"]):
        langue_detectee = "fulfulde"

    hymne_response = LOCAL_KNOWLEDGE["hymne_francais"]

    # Si une langue est détectée et qu'on a l'audio
    if langue_detectee and langue_detectee in audio_index:
        audio_url = f"http://localhost:8000/audio/{audio_index[langue_detectee]['filename']}"
        hymne_response += f"\n\n🎵 **Version audio en {audio_index[langue_detectee]['langue'].title()}** :\n"
        hymne_response += f"▶️ AUDIO: {audio_url}"
        # Retourner un dict pour que l'endpoint puisse gérer l'audio
        return {"text": hymne_response, "audio_url": audio_url, "langue": langue_detectee}
    else:
        # Pas de langue spécifiée, demander de préciser
        hymne_response += "\n\n🎵 **Versions audio disponibles** :\n"
        hymne_response += "Veuillez préciser la langue souhaitée :\n"
        if "moore" in audio_index:
            hymne_response += f"- En Moore : dites 'hymne en moore'\n"
        # ... etc
        return {"text": hymne_response}
```

**Format de Retour**:
- **Ancien**: String simple
- **Nouveau**: Dict avec `{"text": "...", "audio_url": "...", "langue": "..."}`

### 2. Endpoint `/ask` (lignes 308-348)

**Gère le nouveau format**:
```python
local_answer = check_local_knowledge(question)
if local_answer:
    # Gérer le nouveau format avec audio (dict) ou ancien format (string)
    if isinstance(local_answer, dict):
        response_data = {
            "question": question,
            "retrieved_passages": [],
            "scores": [],
            "response": local_answer.get("text", local_answer)
        }
        # Ajouter l'URL audio si disponible
        if "audio_url" in local_answer:
            response_data["audio_url"] = local_answer["audio_url"]
            response_data["audio_langue"] = local_answer.get("langue", "")
        return response_data
```

### 3. Endpoint `/text/ask` (lignes 530-599)

**Utilise l'audio pré-enregistré au lieu de TTS**:
```python
local_answer = check_local_knowledge(question)
audio_prerecorded = None

if local_answer:
    if isinstance(local_answer, dict):
        response_text = local_answer.get("text", "")
        # Vérifier si on a un audio pré-enregistré
        if "audio_url" in local_answer:
            audio_prerecorded = local_answer["audio_url"]
    else:
        response_text = local_answer

# Gérer l'audio
if request.enable_voice:
    # Si on a un audio pré-enregistré (hymne), l'utiliser directement
    if audio_prerecorded:
        response_data["tts_url"] = audio_prerecorded.replace("http://localhost:8000", "")
    else:
        # Sinon générer TTS comme avant
        # ...
```

---

## 🧪 Tests de Validation

### Test 1: Sans Langue Spécifiée
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hymne national"}'
```

**Résultat**: ✅ Demande de préciser la langue

### Test 2: Hymne en Moore
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hymne en moore"}'
```

**Résultat**: ✅ Texte + `audio_url: http://localhost:8000/audio/moore.mp3`

### Test 3: Hymne en Dioula
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hymne en dioula"}'
```

**Résultat**: ✅ Texte + `audio_url: http://localhost:8000/audio/dioula.mp3`

### Test 4: Hymne en Fulfulde
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hymne en fulfulde"}'
```

**Résultat**: ✅ Texte + `audio_url: http://localhost:8000/audio/fulfulde.mp3`

### Test 5: Interface Web
```bash
curl -X POST "http://localhost:8000/text/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hymne en moore","enable_voice":true}'
```

**Résultat**: ✅ `tts_url: /audio/moore.mp3` (audio pré-enregistré)

---

## 🎯 Cas d'Usage

### Cas 1: Utilisateur demande l'hymne sans préciser
```
User: "Hymne national du Burkina Faso"
Bot: [Texte de l'hymne]
     🎵 Versions audio disponibles :
     Veuillez préciser la langue souhaitée :
     - En Moore : dites 'hymne en moore'
     - En Dioula : dites 'hymne en dioula'
     - En Fulfulde : dites 'hymne en fulfulde'

User: "Hymne en moore"
Bot: [Texte de l'hymne]
     🎵 Version audio en Moore :
     ▶️ AUDIO: http://localhost:8000/audio/moore.mp3
     [Lecture automatique de l'audio]
```

### Cas 2: Utilisateur demande directement avec la langue
```
User: "Je veux entendre l'hymne en dioula"
Bot: [Texte de l'hymne]
     🎵 Version audio en Dioula :
     ▶️ AUDIO: http://localhost:8000/audio/dioula.mp3
     [Lecture automatique de l'audio]
```

### Cas 3: Utilisateur demande en français
```
User: "Hymne national en français"
Bot: [Texte de l'hymne en français]
     (Pas d'audio pré-enregistré en français)
```

---

## 📊 Comparaison Avant/Après

### AVANT

**Question**: "Hymne en moore"
**Réponse**:
```
L'Hymne National du Burkina Faso, LE DITANYÉ :
[Texte complet...]

🎵 Versions audio disponibles :
- En Moore : http://localhost:8000/audio/moore.mp3 ← Lien seulement
- En Dioula : http://localhost:8000/audio/dioula.mp3
- En Fulfulde : http://localhost:8000/audio/fulfulde.mp3
```

### APRÈS

**Question**: "Hymne en moore"
**Réponse**:
```
L'Hymne National du Burkina Faso, LE DITANYÉ :
[Texte complet...]

🎵 Version audio en Moore :
▶️ AUDIO: http://localhost:8000/audio/moore.mp3 ← Audio direct

+ Dans la réponse JSON:
  "audio_url": "http://localhost:8000/audio/moore.mp3",
  "audio_langue": "moore"
  → Permet lecture automatique par l'interface
```

---

## 🔧 Configuration

### Ajouter une Nouvelle Langue

1. **Ajouter le fichier audio**:
```bash
cp nouvelle_langue.mp3 static/audio/
```

2. **Mettre à jour `audio_index.json`**:
```json
{
  "nouvelle_langue": {
    "filename": "nouvelle_langue.mp3",
    "langue": "nouvelle_langue",
    ...
  }
}
```

3. **Ajouter la détection dans `check_local_knowledge()`**:
```python
elif any(word in question_lower for word in ["nouvelle_langue", "alias"]):
    langue_detectee = "nouvelle_langue"
```

---

## 📚 Documentation Connexe

- **INTEGRATION_AUDIO_HYMNE.md** → Intégration initiale des fichiers audio
- **CORRECTIFS_APPLIQUES.md** → Correctifs des réponses bizarres
- **GUIDE_CONFIGURATION.md** → Configuration des modèles et voix

---

## ✨ Avantages du Système Interactif

1. **Intelligent**: Détecte automatiquement la langue demandée
2. **Guidé**: Propose les options si langue non spécifiée
3. **Performant**: Utilise audio pré-enregistré (pas de génération TTS)
4. **Multilingue**: Support de 3 langues locales
5. **Compatible**: Fonctionne avec API REST et interface web
6. **Optimisé**: Économise les ressources en évitant la génération TTS

---

**Statut Final**: ✅ Système interactif complet et opérationnel

Les utilisateurs peuvent maintenant:
- ✅ Demander l'hymne sans préciser → Système propose les langues
- ✅ Demander l'hymne avec langue → Audio direct + texte
- ✅ Lecture automatique dans l'interface web (audio pré-enregistré)
- ✅ Détection flexible (moore, mooré, dioula, jula, fulfulde, peul, etc.)
