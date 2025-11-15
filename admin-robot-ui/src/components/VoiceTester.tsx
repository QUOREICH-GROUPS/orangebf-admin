import { FC, useRef, useState } from 'react';
import { api } from '../services/api';
import { useNotifications } from '../context/Notifications';
import { LanguageFilter } from '../context/Filters';

const languageOptions: { value: LanguageFilter | 'en'; label: string }[] = [
  { value: 'fr', label: 'Français' },
  { value: 'moore', label: 'Mooré' },
  { value: 'dioula', label: 'Dioula' },
  { value: 'fulfulde', label: 'Fulfuldé' },
  { value: 'en', label: 'English' }
];

const voiceOptions = [
  { id: 'fr-FR-HenriNeural', label: 'Henri (Masculin)' },
  { id: 'fr-FR-DeniseNeural', label: 'Denise (Féminin)' },
  { id: 'fr-FR-AlainNeural', label: 'Alain (Grave)' },
  { id: 'fr-FR-EloiseNeural', label: 'Éloise (Chaleureuse)' }
];

const VoiceTester: FC = () => {
  const [question, setQuestion] = useState('Comment activer Orange Money ?');
  const [response, setResponse] = useState('');
  const [status, setStatus] = useState('');
  const [language, setLanguage] = useState<LanguageFilter | 'en'>('fr');
  const [voice, setVoice] = useState(voiceOptions[0].id);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { notify } = useNotifications();

  const handleAsk = async () => {
    if (!question.trim()) return;
    setStatus('🧠 RAG en cours...');
    try {
      const data = await api.askQuestion(question.trim(), { language });
      setResponse(data.text || data.response || '');
      setStatus('✅ Réponse reçue');
      setAudioUrl(null);
      notify('success', 'Réponse générée');
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handleTTS = async () => {
    if (!response) return;
    setStatus('🔊 Génération audio...');
    try {
      const blob = await api.speakEdge(response, voice);
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setStatus('✅ Audio prêt');
      notify('success', 'Audio généré avec Edge-TTS');
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handlePlay = () => {
    audioRef.current?.play();
  };

  const handlePause = () => {
    audioRef.current?.pause();
  };

  const handleSave = () => {
    if (!audioUrl) return;
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = 'demo_voice.mp3';
    link.click();
  };

  return (
    <section className="card">
      <h2>4️⃣ Test du système de dialogue</h2>
      <p>Choisir un prompt, générer la réponse, puis écouter la synthèse vocale.</p>
      <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
      <div className="form-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <label>
          Langue de réponse
          <select value={language} onChange={(event) => setLanguage(event.target.value as LanguageFilter | 'en')}>
            {languageOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Voix Edge-TTS
          <select value={voice} onChange={(event) => setVoice(event.target.value)}>
            {voiceOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button className="btn primary" type="button" onClick={handleAsk}>
          Envoyer la question
        </button>
        <button className="btn" type="button" onClick={handleTTS} disabled={!response}>
          Lire la réponse
        </button>
      </div>
      <div className="status-pill" style={{ background: 'rgba(148,148,148,0.15)' }}>{status || 'Prêt'}</div>
      {response && (
        <div className="log-entry" style={{ marginTop: 12 }}>
          <strong>Réponse:</strong>
          <br />
          {response}
        </div>
      )}
      {audioUrl && (
        <div style={{ marginTop: 12 }}>
          <audio src={audioUrl} controls style={{ width: '100%' }} ref={audioRef}>
            Votre navigateur ne supporte pas l'audio.
          </audio>
          <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
            <button className="btn" type="button" onClick={handlePlay}>
              ▶️ Play
            </button>
            <button className="btn" type="button" onClick={handlePause}>
              ⏸ Stop
            </button>
            <button className="btn" type="button" onClick={handleSave}>
              💾 Enregistrer
            </button>
          </div>
        </div>
      )}
    </section>
  );
};

export default VoiceTester;
