import { ChangeEvent, FC, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../services/api';
import { useNotifications } from '../context/Notifications';
import { useFilters } from '../context/Filters';

interface AudioEntry {
  id?: string;
  filename: string;
  description?: string;
  categorie?: string;
  langue?: string;
  size_mb?: number;
}

interface SalutationMap {
  [lang: string]: Record<string, string | string[]>;
}

interface CustomGreeting {
  id: string;
  language: string;
  timeOfDay: string;
  message: string;
  context: string;
}

const createGreetingId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const voiceOptions = [
  { id: 'fr-FR-HenriNeural', label: 'Henri (masculin)' },
  { id: 'fr-FR-DeniseNeural', label: 'Denise (féminin)' },
  { id: 'fr-FR-AlainNeural', label: 'Alain (grave)' },
  { id: 'fr-FR-EloiseNeural', label: 'Éloise (chaleureuse)' }
];

const UserGreetings: FC = () => {
  const [audios, setAudios] = useState<AudioEntry[]>([]);
  const [salutations, setSalutations] = useState<SalutationMap>({});
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [customGreetings, setCustomGreetings] = useState<CustomGreeting[]>([]);
  const [editing, setEditing] = useState<CustomGreeting | null>(null);
  const [previewMessage, setPreviewMessage] = useState('Bonjour et bienvenue chez Orange Burkina Faso !');
  const [previewVoice, setPreviewVoice] = useState(voiceOptions[0].id);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewStatus, setPreviewStatus] = useState('');
  const previewRef = useRef<HTMLAudioElement | null>(null);
  const { notify } = useNotifications();
  const { language: globalLanguage } = useFilters();

  const loadAudios = async () => {
    try {
      const data = await api.getAudioIndex();
      setAudios(Object.values(data.files || {}));
      notify('success', 'Bibliothèque audio chargée');
    } catch (error) {
      const message = (error as Error).message;
      setStatus(message);
      notify('error', message);
    }
  };

  const loadSalutations = async () => {
    try {
      const data = await api.getSalutations();
      setSalutations(data.data || {});
    } catch (error) {
      console.error('Salutation error', error);
    }
  };

  useEffect(() => {
    loadAudios();
    loadSalutations();
    const stored = localStorage.getItem('custom_greetings');
    if (stored) {
      setCustomGreetings(JSON.parse(stored));
    }
  }, []);

  const persistGreetings = (next: CustomGreeting[]) => {
    setCustomGreetings(next);
    localStorage.setItem('custom_greetings', JSON.stringify(next));
  };

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    setStatus('Téléversement en cours...');
    try {
      await api.uploadAudio(formData);
      setStatus('✅ Audio ajouté');
      notify('success', 'Audio importé');
      form.reset();
      loadAudios();
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handleDelete = async (audioId: string) => {
    if (!confirm('Supprimer cet audio ?')) return;
    try {
      await api.deleteAudio(audioId);
      notify('success', 'Audio supprimé');
      loadAudios();
    } catch (error) {
      notify('error', (error as Error).message);
    }
  };

  const handleConvert = async (audioId: string) => {
    try {
      await api.convertAudio(audioId);
      notify('info', 'Conversion WAV lancée');
      loadAudios();
    } catch (error) {
      notify('error', (error as Error).message);
    }
  };

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => setSearch(event.target.value);

  const filteredAudios = useMemo(() => {
    const lower = search.toLowerCase();
    return audios.filter((audio) => {
      const matchesSearch =
        !lower ||
        audio.description?.toLowerCase().includes(lower) ||
        audio.filename.toLowerCase().includes(lower) ||
        audio.langue?.toLowerCase().includes(lower || '');
      const matchesLanguage =
        globalLanguage === 'all' || audio.langue?.toLowerCase() === globalLanguage.toLowerCase();
      return matchesSearch && matchesLanguage;
    });
  }, [audios, search, globalLanguage]);

  const filteredGreetings = useMemo(() => {
    if (globalLanguage === 'all') return customGreetings;
    return customGreetings.filter((g) => g.language === globalLanguage);
  }, [customGreetings, globalLanguage]);

  const handleGreetingSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const payload: CustomGreeting = {
      id: editing?.id || createGreetingId(),
      language: (data.get('greeting_lang') as string) || 'fr',
      timeOfDay: (data.get('greeting_time') as string) || 'matin',
      message: (data.get('greeting_message') as string) || '',
      context: (data.get('greeting_context') as string) || ''
    };
    if (!payload.message.trim()) {
      notify('error', 'Veuillez saisir un message.');
      return;
    }
    const next = editing
      ? customGreetings.map((item) => (item.id === editing.id ? payload : item))
      : [...customGreetings, payload];
    persistGreetings(next);
    notify('success', editing ? 'Salutation modifiée (locale)' : 'Salutation ajoutée (locale)');
    setEditing(null);
    form.reset();
  };

  const editGreeting = (greeting: CustomGreeting) => {
    setEditing(greeting);
    setPreviewMessage(greeting.message);
  };

  const deleteGreeting = (id: string) => {
    persistGreetings(customGreetings.filter((item) => item.id !== id));
    notify('success', 'Salutation supprimée (locale)');
  };

  const handlePreview = async (message: string) => {
    setPreviewStatus('Synthèse en cours...');
    try {
      const blob = await api.speakEdge(message, previewVoice);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setPreviewStatus('✅ Audio généré');
      setTimeout(() => previewRef.current?.play(), 50);
    } catch (error) {
      notify('error', (error as Error).message);
      setPreviewStatus('❌ Erreur');
    }
  };

  const stopPreview = () => previewRef.current?.pause();

  return (
    <section className="card">
      <h2>3️⃣ Audios & Salutations</h2>
      <p>Uploader l'hymne, les salutations ou les phrases pré-enregistrées.</p>
      <form onSubmit={handleUpload} className="form-grid">
        <label>
          Catégorie
          <select name="category">
            <option value="hymne_national">Hymne national</option>
            <option value="salutation">Salutation</option>
            <option value="phrase">Phrase clé</option>
            <option value="reponse_fix">Réponse fixe</option>
          </select>
        </label>
        <label>
          Langue
          <select name="langue">
            <option value="fr">Français</option>
            <option value="moore">Mooré</option>
            <option value="dioula">Dioula</option>
            <option value="fulfulde">Fulfuldé</option>
          </select>
        </label>
        <label>
          Description
          <input type="text" name="description" placeholder="Ex: Hymne officiel en Mooré" />
        </label>
        <label>
          <input type="checkbox" name="convert_wav" /> Convertir en WAV après upload
        </label>
        <label>
          Fichier audio
          <input type="file" name="file" accept="audio/*" required />
        </label>
        <button className="btn primary" type="submit">
          🎵 Ajouter l'audio
        </button>
        <div className="status-pill" style={{ background: 'rgba(148,148,148,0.15)' }}>{status || 'Prêt'}</div>
      </form>

      <div className="form-grid" style={{ marginTop: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
            <h3>Bibliothèque audio ({audios.length})</h3>
            <input type="search" placeholder="Filtrer un audio..." value={search} onChange={handleSearchChange} />
          </div>
          <div className="list-scroll">
            {filteredAudios.map((audio) => {
              const id = audio.id || audio.langue || audio.filename;
              return (
                <div key={id} className="log-entry">
                  <strong>{audio.description || audio.filename}</strong>
                  <br />
                  <small>
                    {audio.categorie || 'n/a'} • {audio.langue || '??'} • {audio.size_mb ?? 0} MB
                  </small>
                  <audio controls src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/audio/${audio.filename}`} style={{ width: '100%', marginTop: 8 }} />
                  <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                    <button className="btn" type="button" onClick={() => handleConvert(id)}>
                      Convertir WAV
                    </button>
                    <button className="btn danger" type="button" onClick={() => handleDelete(id)}>
                      Supprimer
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div>
          <h3>Salutations automatiques</h3>
          <form onSubmit={handleGreetingSubmit} className="form-grid" key={editing?.id || 'new'}>
            <label>
              Langue
              <select name="greeting_lang" defaultValue={editing?.language || 'fr'}>
                <option value="fr">Français</option>
                <option value="moore">Mooré</option>
                <option value="dioula">Dioula</option>
                <option value="fulfulde">Fulfuldé</option>
              </select>
            </label>
            <label>
              Moment de la journée
              <select name="greeting_time" defaultValue={editing?.timeOfDay || 'matin'}>
                <option value="matin">Matin</option>
                <option value="midi">Après-midi</option>
                <option value="soir">Soir</option>
                <option value="nuit">Nuit</option>
              </select>
            </label>
            <label>
              Message
              <textarea name="greeting_message" defaultValue={editing?.message || ''} placeholder="Bonjour, bienvenue chez Orange Faso !" />
            </label>
            <label>
              Contexte
              <input name="greeting_context" defaultValue={editing?.context || ''} placeholder="Ex: Accueil boutique, client VIP..." />
            </label>
            <button className="btn primary" type="submit">
              {editing ? 'Modifier' : 'Ajouter'}
            </button>
          </form>

          <div className="list-scroll" style={{ marginTop: 16 }}>
            {filteredGreetings.length === 0 && <p>Aucune salutation personnalisée.</p>}
            {filteredGreetings.map((greeting) => (
              <div key={greeting.id} className="log-entry">
                <strong>
                  {greeting.language.toUpperCase()} • {greeting.timeOfDay}
                </strong>
                <p>{greeting.message}</p>
                <small>{greeting.context}</small>
                <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                  <button className="btn" type="button" onClick={() => editGreeting(greeting)}>
                    Modifier
                  </button>
                  <button className="btn" type="button" onClick={() => handlePreview(greeting.message)}>
                    Tester
                  </button>
                  <button className="btn danger" type="button" onClick={() => deleteGreeting(greeting.id)}>
                    Supprimer
                  </button>
                </div>
              </div>
            ))}
          </div>
          <h4>Salutations système</h4>
          <div className="list-scroll">
            {Object.keys(salutations).length === 0 && <p>Aucune salutation chargée.</p>}
            {Object.entries(salutations).map(([langue, expressions]) => (
              <div key={langue} className="log-entry">
                <strong>{langue.toUpperCase()}</strong>
                <ul>
                  {Object.entries(expressions).map(([key, value]) => (
                    <li key={key}>
                      {key}: {Array.isArray(value) ? value.join(', ') : value}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ border: '1px dashed var(--border)' }}>
        <h3>Tester une salutation (TTS)</h3>
        <p>Utilise les voix Edge-TTS pour pré-écouter un message, comme dans le module RAG.</p>
        <textarea value={previewMessage} onChange={(event) => setPreviewMessage(event.target.value)} />
        <label>
          Voix
          <select value={previewVoice} onChange={(event) => setPreviewVoice(event.target.value)}>
            {voiceOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 10 }}>
          <button className="btn primary" type="button" onClick={() => handlePreview(previewMessage)}>
            Générer
          </button>
          <button className="btn" type="button" onClick={stopPreview} disabled={!previewUrl}>
            Stop
          </button>
          <button className="btn" type="button" disabled={!previewUrl} onClick={() => previewRef.current?.play()}>
            Play
          </button>
          <button
            className="btn"
            type="button"
            disabled={!previewUrl}
            onClick={() => {
              if (!previewUrl) return;
              const link = document.createElement('a');
              link.href = previewUrl;
              link.download = 'greeting_preview.mp3';
              link.click();
            }}
          >
            Save
          </button>
        </div>
        <div className="status-pill" style={{ background: 'rgba(148,148,148,0.15)', marginTop: 10 }}>
          {previewStatus || 'Prêt'}
        </div>
        {previewUrl && (
          <audio controls src={previewUrl} ref={previewRef} style={{ marginTop: 10, width: '100%' }}>
            Aperçu non supporté.
          </audio>
        )}
      </div>
    </section>
  );
};

export default UserGreetings;
