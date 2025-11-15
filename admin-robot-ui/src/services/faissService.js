const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const requestJSON = async (path, options) => {
  const res = await fetch(`${API_URL}${path}`, options);
  if (!res.ok) {
    let detail;
    try {
      const data = await res.json();
      detail = data.detail || data.message;
    } catch {
      detail = await res.text();
    }
    throw new Error(detail || res.statusText);
  }
  return res.json();
};

export const faissService = {
  listDocuments: async () => {
    const data = await requestJSON('/knowledge/documents');
    return data.documents || [];
  },
  uploadDocument: async (formData) => requestJSON('/knowledge/documents', { method: 'POST', body: formData }),
  getSegments: async (docId) => {
    const data = await requestJSON(`/knowledge/segments/${docId}`);
    return data.segments || [];
  },
  reindexDocument: async (docId) => requestJSON(`/knowledge/documents/${docId}/reindex`, { method: 'POST' }),
  deleteDocument: async (docId) => requestJSON(`/knowledge/documents/${docId}`, { method: 'DELETE' })
};

export default faissService;
