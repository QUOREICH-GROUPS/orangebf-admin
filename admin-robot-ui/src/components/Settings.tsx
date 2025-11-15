import { FC, useEffect, useState } from 'react';
import { api } from '../services/api';
import { useNotifications } from '../context/Notifications';

const LOCAL_DIALOGUE_KEY = 'local_dialogue_settings';
const LOCAL_NETWORK_KEY = 'local_network_settings';

interface DialogueSettings {
  llm_model: string;
  stt_engine: string;
  tts_engine: string;
  voice_profile?: string;
  auto_play?: boolean;
}

interface DialogueOptions {
  llm_models: string[];
  stt_engines: string[];
  tts_engines: string[];
  voice_profiles: string[];
}

interface NetworkSettings {
  connection: string;
  ethernet_ip?: string;
  wifi?: Record<string, string>;
  mqtt?: Record<string, string>;
  websocket_url?: string;
  microphone_enabled?: boolean;
  camera_enabled?: boolean;
}

interface CapabilitiesResponse {
  stt?: {
    current?: string;
    engines?: string[];
  };
  tts?: {
    current?: string;
    engines?: string[];
  };
  llm?: {
    provider?: string;
    model?: string;
  };
  rag?: {
    index_size?: number;
    top_k?: number;
  };
}

const Settings: FC = () => {
  const [dialogueSettings, setDialogueSettings] = useState<DialogueSettings | null>(null);
  const [dialogueOptions, setDialogueOptions] = useState<DialogueOptions | null>(null);
  const [networkSettings, setNetworkSettings] = useState<NetworkSettings | null>(null);
  const [status, setStatus] = useState('');
  const [dialogueAvailable, setDialogueAvailable] = useState(true);
  const [networkAvailable, setNetworkAvailable] = useState(true);
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);
  const [healthInfo, setHealthInfo] = useState<Record<string, unknown> | null>(null);
  const [dialogueDraft, setDialogueDraft] = useState<DialogueSettings | null>(null);
  const [networkDraft, setNetworkDraft] = useState<NetworkSettings | null>(null);
  const { notify } = useNotifications();

  const defaultOptions: DialogueOptions = {
    llm_models: ['llama-3.1-8b-instant', 'mixtral-8x7b', 'llama-3.1-70b-versatile'],
    stt_engines: ['faster-whisper', 'whisper', 'vosk'],
    tts_engines: ['piper', 'espeak'],
    voice_profiles: ['piper_fr', 'edge_henri']
  };

  useEffect(() => {
    if (!dialogueOptions) {
      setDialogueOptions(defaultOptions);
    }
  }, []);

  const hydrateLocalDialogue = (caps?: CapabilitiesResponse): DialogueSettings => {
    const stored = localStorage.getItem(LOCAL_DIALOGUE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return {
      llm_model: caps?.llm?.model || 'llama-3.1-8b-instant',
      stt_engine: caps?.stt?.current || 'faster-whisper',
      tts_engine: caps?.tts?.current || 'piper',
      voice_profile: caps?.tts?.current === 'espeak' ? 'edge_henri' : 'piper_fr',
      auto_play: true
    };
  };

  const hydrateLocalNetwork = (): NetworkSettings => {
    const stored = localStorage.getItem(LOCAL_NETWORK_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return {
      connection: 'ethernet',
      ethernet_ip: '',
      wifi: { ssid: '', status: '' },
      mqtt: { broker: '', topic: '' },
      websocket_url: '',
      microphone_enabled: true,
      camera_enabled: true
    };
  };

  const loadSettings = async () => {
    setStatus('Synchronisation des paramètres...');

    const handleNotFound = (error: Error, label: 'dialogue' | 'network') => {
      if (error.message.includes('Not Found')) {
        if (label === 'dialogue') {
          setDialogueAvailable(false);
        } else {
          setNetworkAvailable(false);
        }
        notify('info', `Endpoints ${label} indisponibles sur ce backend.`);
        return;
      }
      throw error;
    };

    try {
      const [capsData, healthData] = await Promise.all([
        api.getCapabilities().catch(() => null),
        api.getHealth().catch(() => null)
      ]);
      if (capsData) {
        setCapabilities(capsData);
      }
      if (healthData) {
        setHealthInfo(healthData);
      }

      await Promise.all([
        api
          .getDialogueSettings()
          .then((dialogue) => {
            setDialogueSettings(dialogue.settings);
            setDialogueOptions(dialogue.options);
            setDialogueDraft(dialogue.settings);
            setDialogueAvailable(true);
          })
          .catch((error: Error) => {
            handleNotFound(error, 'dialogue');
            const fallback = hydrateLocalDialogue(capsData || undefined);
            setDialogueDraft(fallback);
            setDialogueOptions(dialogueOptions || defaultOptions);
          }),
        api
          .getNetworkSettings()
          .then((network) => {
            setNetworkSettings(network.settings);
            setNetworkDraft(network.settings);
            setNetworkAvailable(true);
          })
          .catch((error: Error) => {
            handleNotFound(error, 'network');
            setNetworkDraft(hydrateLocalNetwork());
          })
      ]);
      setStatus('');
    } catch (error) {
      const message = (error as Error).message;
      setStatus(message);
      notify('error', message);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const updateDialogue = (key: keyof DialogueSettings, value: string | boolean) => {
    setDialogueDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const saveDialogue = async () => {
    if (!dialogueDraft) return;
    setStatus('Sauvegarde des paramètres dialogue...');
    try {
      if (dialogueAvailable) {
        await api.updateDialogueSettings(dialogueDraft);
        setStatus('✅ Paramètres dialogue mis à jour');
        notify('success', 'Dialogue mis à jour');
      } else {
        localStorage.setItem(LOCAL_DIALOGUE_KEY, JSON.stringify(dialogueDraft));
        setStatus('✅ Paramètres locaux sauvegardés');
        notify('success', 'Paramètres sauvegardés localement (à appliquer lors du déploiement).');
      }
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const updateNetwork = (key: keyof NetworkSettings, value: string | boolean) => {
    setNetworkDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const saveNetwork = async () => {
    if (!networkDraft) return;
    setStatus('Sauvegarde des paramètres réseau...');
    try {
      if (networkAvailable) {
        await api.updateNetworkSettings(networkDraft);
        setStatus('✅ Paramètres réseau mis à jour');
        notify('success', 'Réseau mis à jour');
      } else {
        localStorage.setItem(LOCAL_NETWORK_KEY, JSON.stringify(networkDraft));
        setStatus('✅ Paramètres réseau sauvegardés localement');
        notify('success', 'Paramètres réseau sauvegardés (à reporter lorsque les endpoints seront actifs).');
      }
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  return (
    <section className="card">
      <h2>5️⃣ Paramètres du robot</h2>
      <div className="status-pill" style={{ background: 'rgba(148,148,148,0.15)' }}>{status || 'Prêt'}</div>

      {dialogueDraft && dialogueOptions ? (
        dialogueAvailable ? (
          <div style={{ marginBottom: 24 }}>
            <h3>Dialogue (LLM + TTS)</h3>
            <div className="form-grid">
              <label>
                Modèle LLM
                <select value={dialogueDraft.llm_model} onChange={(e) => updateDialogue('llm_model', e.target.value)}>
                  {dialogueOptions.llm_models.filter(Boolean).map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Moteur STT
                <select value={dialogueDraft.stt_engine} onChange={(e) => updateDialogue('stt_engine', e.target.value)}>
                  {dialogueOptions.stt_engines.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Moteur TTS
                <select value={dialogueDraft.tts_engine} onChange={(e) => updateDialogue('tts_engine', e.target.value)}>
                  {dialogueOptions.tts_engines.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Profil voix
                <input
                  type="text"
                  value={dialogueDraft.voice_profile || ''}
                  onChange={(e) => updateDialogue('voice_profile', e.target.value)}
                />
              </label>
              <label>
                Lecture auto
                <select
                  value={dialogueDraft.auto_play ? 'true' : 'false'}
                  onChange={(e) => updateDialogue('auto_play', e.target.value === 'true')}
                >
                  <option value="true">Activée</option>
                  <option value="false">Désactivée</option>
                </select>
              </label>
            </div>
            <button className="btn primary" type="button" onClick={saveDialogue} style={{ marginTop: 12 }}>
              Sauvegarder dialogue
            </button>
          </div>
        ) : (
          <div className="read-only-card">
            <p>Endpoints dialogue non exposés par ce backend (édition locale uniquement).</p>
            {capabilities?.llm && (
              <ul>
                <li>
                  <strong>Fournisseur LLM :</strong> {capabilities.llm.provider || 'N/A'}
                </li>
                <li>
                  <strong>Modèle :</strong> {capabilities.llm.model || 'N/A'}
                </li>
              </ul>
            )}
            <p style={{ color: 'var(--muted)' }}>
              Les valeurs saisies seront sauvegardées côté navigateur et pourront être envoyées lors du passage à
              `rag_server_voice.py`.
            </p>
            <button className="btn primary" type="button" onClick={saveDialogue}>
              Sauvegarder localement
            </button>
          </div>
        )
      ) : (
        <p>Chargement des paramètres dialogue...</p>
      )}

      {networkDraft ? (
        networkAvailable ? (
          <div>
            <h3>Réseau & capteurs</h3>
            <div className="form-grid">
              <label>
                Connexion
                <select value={networkDraft.connection} onChange={(e) => updateNetwork('connection', e.target.value)}>
                  <option value="ethernet">Ethernet</option>
                  <option value="wifi">WiFi</option>
                </select>
              </label>
              <label>
                IP Ethernet
                <input
                  type="text"
                  value={networkDraft.ethernet_ip || ''}
                  onChange={(e) => updateNetwork('ethernet_ip', e.target.value)}
                />
              </label>
              <label>
                Websocket URL
                <input
                  type="text"
                  value={networkDraft.websocket_url || ''}
                  onChange={(e) => updateNetwork('websocket_url', e.target.value)}
                />
              </label>
              <label>
                Microphone actif ?
                <select
                  value={networkDraft.microphone_enabled ? 'true' : 'false'}
                  onChange={(e) => updateNetwork('microphone_enabled', e.target.value === 'true')}
                >
                  <option value="true">Oui</option>
                  <option value="false">Non</option>
                </select>
              </label>
              <label>
                Caméra active ?
                <select
                  value={networkDraft.camera_enabled ? 'true' : 'false'}
                  onChange={(e) => updateNetwork('camera_enabled', e.target.value === 'true')}
                >
                  <option value="true">Oui</option>
                  <option value="false">Non</option>
                </select>
              </label>
            </div>
            <button className="btn primary" type="button" onClick={saveNetwork} style={{ marginTop: 12 }}>
              Sauvegarder réseau
            </button>
          </div>
        ) : (
          <div className="read-only-card">
            <p>Endpoints réseau non exposés par ce backend (édition locale uniquement).</p>
            {healthInfo && (
              <ul>
                <li>
                  <strong>Plateforme :</strong> {(healthInfo.platform as string) || 'N/A'}
                </li>
                <li>
                  <strong>LLM :</strong> {(healthInfo.llm_model as string) || 'N/A'}
                </li>
              </ul>
            )}
            <p style={{ color: 'var(--muted)' }}>Les paramètres saisis seront sauvegardés côté navigateur.</p>
            <button className="btn primary" type="button" onClick={saveNetwork}>
              Sauvegarder localement
            </button>
          </div>
        )
      ) : (
        <p>Chargement des paramètres réseau...</p>
      )}
    </section>
  );
};

export default Settings;
