const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    let detail;
    try {
      const data = await response.json();
      detail = data.detail || data.message;
    } catch (err) {
      detail = await response.text();
    }
    throw new Error(detail || response.statusText);
  }
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response;
}

export const api = {
  getHealth: () => request('/health'),
  getStats: () => request('/stats'),
  getMetrics: () => request('/admin/metrics'),
  getCapabilities: () => request('/capabilities'),
  restartRobot: () => request('/admin/restart', { method: 'POST' }),
  getDialogueSettings: () => request('/settings/dialogue'),
  updateDialogueSettings: (payload) =>
    request('/settings/dialogue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),
  getNetworkSettings: () => request('/settings/network'),
  updateNetworkSettings: (payload) =>
    request('/settings/network', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }),
  getAudioIndex: () => request('/audio_index'),
  uploadAudio: (formData) => request('/audio/upload', { method: 'POST', body: formData }),
  deleteAudio: (audioId) => request(`/audio/${audioId}`, { method: 'DELETE' }),
  convertAudio: (audioId) => request(`/audio/${audioId}/convert`, { method: 'POST' }),
  getSalutations: () => request('/salutations'),
  askQuestion: (question, options = {}) =>
    request('/text/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, enable_voice: false, ...options })
    }),
  generateTTS: async (text, lang = 'fr') => {
    const res = await request(`/tts?text=${encodeURIComponent(text)}&lang=${lang}`);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },
  speakEdge: async (text, voice) => {
    const res = await request('/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice })
    });
    const blob = await res.blob();
    return blob;
  },
  voiceAsk: (formData) =>
    request('/voice/ask', {
      method: 'POST',
      body: formData
    }),
  simpleAsk: (question) =>
    request('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    }),
  transcribeAudio: (file, language = 'fr') => {
    const formData = new FormData();
    formData.append('file', file, 'message.webm');
    formData.append('language', language);
    return request('/transcribe', {
      method: 'POST',
      body: formData
    });
  }
};

export default api;
