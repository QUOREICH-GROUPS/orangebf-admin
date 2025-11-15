import { FC, useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { useNotifications } from '../context/Notifications';
import { LanguageFilter } from '../context/Filters';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  audioUrl?: string;
  timestamp: string;
}

const languages: { value: LanguageFilter | 'en'; label: string }[] = [
  { value: 'fr', label: 'Français' },
  { value: 'moore', label: 'Mooré' },
  { value: 'dioula', label: 'Dioula' },
  { value: 'fulfulde', label: 'Fulfuldé' },
  { value: 'en', label: 'Anglais' }
];

const LiveChat: FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState<LanguageFilter | 'en'>('fr');
  const [autoVoice, setAutoVoice] = useState(true);
  const [mode, setMode] = useState<'rag' | 'llm'>('rag');
  const [isSending, setIsSending] = useState(false);
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const { notify } = useNotifications();
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [fullScreen, setFullScreen] = useState(false);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const { body } = document;
    if (fullScreen) {
      body.classList.add('live-chat-locked');
    } else {
      body.classList.remove('live-chat-locked');
    }
    return () => body.classList.remove('live-chat-locked');
  }, [fullScreen]);

  const appendMessage = (message: Message) => setMessages((prev) => [...prev, message]);

  const askAssistant = async (questionText: string) => {
    setIsSending(true);
    try {
      if (mode === 'rag') {
        const data = await api.askQuestion(questionText, { language });
        const text = data.text || data.response || '(Aucune réponse)';
        appendMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          text,
          timestamp: new Date().toISOString()
        });
        if (autoVoice) {
          const blob = await api.speakEdge(text, 'fr-FR-HenriNeural');
          appendMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            text: '[Audio généré]',
            audioUrl: URL.createObjectURL(blob),
            timestamp: new Date().toISOString()
          });
        }
      } else {
        const data = await api.simpleAsk(questionText);
        const text = data.response || data.answer || '(Aucune réponse)';
        appendMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          text,
          timestamp: new Date().toISOString()
        });
        if (autoVoice) {
          const blob = await api.speakEdge(text, 'fr-FR-HenriNeural');
          appendMessage({
            id: crypto.randomUUID(),
            role: 'assistant',
            text: '[Audio généré]',
            audioUrl: URL.createObjectURL(blob),
            timestamp: new Date().toISOString()
          });
        }
      }
    } catch (error) {
      notify('error', (error as Error).message);
    } finally {
      setIsSending(false);
    }
  };

  const sendTextMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    appendMessage({ id: crypto.randomUUID(), role: 'user', text: trimmed, timestamp: new Date().toISOString() });
    setInput('');
    await askAssistant(trimmed);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunks.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.current.push(event.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(audioChunks.current, { type: 'audio/webm' });
        await sendVoiceMessage(blob);
      };
      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (error) {
      notify('error', `Micro indisponible: ${(error as Error).message}`);
    }
  };

  const stopRecording = () => {
    mediaRecorder?.stop();
    setRecording(false);
  };

  const sendVoiceMessage = async (blob: Blob) => {
    try {
      const sttLang = language === 'en' ? 'en' : 'fr';
      const transcription = await api.transcribeAudio(blob, sttLang);
      const userText = typeof transcription === 'string' ? transcription : transcription.text || '(inaudible)';
      appendMessage({
        id: crypto.randomUUID(),
        role: 'user',
        text: userText,
        timestamp: new Date().toISOString()
      });
      await askAssistant(userText);
    } catch (error) {
      notify('error', (error as Error).message);
    }
  };

  return (
    <section className="card live-chat-card">
      <div className="chatgpthero">
        <div className="badge">Live</div>
        <h2>Assistant Orange</h2>
        <p>Testez le robot en direct comme sur ChatGPT / Gemini Live — voix ou texte.</p>
        <div className="hero-actions">
          <select value={mode} onChange={(event) => setMode(event.target.value as 'rag' | 'llm')}>
            <option value="rag">Mode RAG (Orange)</option>
            <option value="llm">Mode LLM Libre</option>
          </select>
          <select value={language} onChange={(event) => setLanguage(event.target.value as LanguageFilter | 'en')}>
            {languages.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select value={autoVoice ? 'true' : 'false'} onChange={(event) => setAutoVoice(event.target.value === 'true')}>
            <option value="true">TTS auto</option>
            <option value="false">Sans TTS</option>
          </select>
          <button type="button" onClick={() => setMessages([])}>
            Effacer
          </button>
        </div>
      </div>

      <div className={`live-wrapper ${fullScreen ? 'fullscreen' : ''}`}>
        <div className="live-header">
          <div className="avatar">
            <span>🤖</span>
          </div>
          <div>
            <strong>{mode === 'rag' ? 'Agent Orange RAG' : 'Assistant LLM Libre'}</strong>
            <small>Disponible maintenant</small>
          </div>
          <button className="header-btn" type="button" onClick={() => setFullScreen((prev) => !prev)}>
            {fullScreen ? '⤡' : '⤢'}
          </button>
        </div>
        <div className="live-messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <h4>Démarrez la session</h4>
              <p>Exprimez-vous en texte ou enregistrez une note vocale pour lancer la conversation.</p>
            </div>
          )}
          {messages.map((message) => (
            <div key={message.id} className={`chat-bubble ${message.role}`}>
              <small>
                {message.role === 'user' ? 'Vous' : 'Robot'} • {new Date(message.timestamp).toLocaleTimeString()}
              </small>
              <p>{message.text}</p>
              {message.audioUrl && (
                <audio className="audio-player" controls src={message.audioUrl}>
                  Aperçu audio
                </audio>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <div className="live-composer">
          <div className="composer-actions">
            <button type="button" title="Ajouter une pièce jointe" disabled>
              📎
            </button>
            <button type="button" onClick={recording ? stopRecording : startRecording}>
              {recording ? '⏹' : '🎤'}
            </button>
          </div>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Décrivez votre situation ou posez une question…"
            disabled={isSending}
          />
          <button className="send-btn" type="button" onClick={sendTextMessage} disabled={isSending}>
            ➤
          </button>
        </div>
      </div>
    </section>
  );
};

export default LiveChat;
