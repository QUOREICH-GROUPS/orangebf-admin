import { ChangeEvent, FC, FormEvent, useEffect, useMemo, useState } from 'react';
import { faissService } from '../services/faissService';
import { useNotifications } from '../context/Notifications';
import { useFilters } from '../context/Filters';
import { api } from '../services/api';

interface DocumentMeta {
  id: string;
  original_name: string;
  category: string;
  segments: number;
  size_mb: number;
  segment_preview?: string;
}

interface Segment {
  text: string;
  order: number;
}

const FAQManager: FC = () => {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>('');
  const [status, setStatus] = useState('');
  const [filter, setFilter] = useState('');
  const [overrides, setOverrides] = useState<Record<string, { title?: string; notes?: string }>>({});
  const [testQuestion, setTestQuestion] = useState('');
  const [testAnswer, setTestAnswer] = useState('');
  const [testing, setTesting] = useState(false);
  const { category, language } = useFilters();
  const { notify } = useNotifications();
  const [isLoading, setIsLoading] = useState(false);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const list = await faissService.listDocuments();
      setDocuments(list);
      notify('success', 'Index FAISS synchronisé');
    } catch (error) {
      const message = (error as Error).message;
      setStatus(message);
      notify('error', message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    const stored = localStorage.getItem('faq_overrides');
    if (stored) {
      setOverrides(JSON.parse(stored));
    }
  }, []);

  const persistOverrides = (next: Record<string, { title?: string; notes?: string }>) => {
    setOverrides(next);
    localStorage.setItem('faq_overrides', JSON.stringify(next));
  };

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    setStatus('⏳ Indexation en cours...');
    try {
      await faissService.uploadDocument(formData);
      setStatus('✅ Document importé');
      notify('success', 'Document importé');
      form.reset();
      loadDocuments();
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handleSelect = async (docId: string) => {
    setSelectedDoc(docId);
    setStatus('Chargement des segments...');
    try {
      const data = await faissService.getSegments(docId);
      setSegments(data);
      setStatus('');
      notify('info', `Segments chargés (${data.length})`);
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handleReindex = async (docId: string) => {
    setStatus('Ré-indexation en cours...');
    try {
      await faissService.reindexDocument(docId);
      setStatus('✅ Ré-indexé');
      notify('success', 'Ré-indexation réussie');
      loadDocuments();
      if (docId === selectedDoc) {
        handleSelect(docId);
      }
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Supprimer ce document ?')) return;
    try {
      await faissService.deleteDocument(docId);
      setStatus('✅ Document supprimé');
      notify('success', 'Document supprimé');
      setSegments([]);
      setSelectedDoc('');
      loadDocuments();
    } catch (error) {
      const message = (error as Error).message;
      setStatus(`❌ ${message}`);
      notify('error', message);
    }
  };

  const handleFilterChange = (event: ChangeEvent<HTMLInputElement>) => setFilter(event.target.value);

  const filteredDocs = useMemo(() => {
    const lower = filter.toLowerCase();
    return documents.filter((doc) => {
      const matchesSearch =
        !lower ||
        doc.original_name.toLowerCase().includes(lower) ||
        doc.category.toLowerCase().includes(lower) ||
        overrides[doc.id]?.notes?.toLowerCase().includes(lower);
      const matchesCategory = category === 'all' || doc.category === category;
      const matchesLanguage =
        language === 'all' ||
        doc.original_name.toLowerCase().includes(language) ||
        overrides[doc.id]?.notes?.toLowerCase().includes(language);
      return matchesSearch && matchesCategory && matchesLanguage;
    });
  }, [documents, filter, category, language, overrides]);

  const updateOverride = (docId: string, field: 'title' | 'notes', value: string) => {
    const next = { ...overrides, [docId]: { ...overrides[docId], [field]: value } };
    persistOverrides(next);
    notify('success', 'Annotation mise à jour (locale)');
  };

  const testFaiss = async () => {
    if (!testQuestion.trim()) return;
    setTesting(true);
    setTestAnswer('');
    try {
      const data = await api.askQuestion(testQuestion.trim());
      setTestAnswer(data.text || data.response || 'Aucune réponse fournie.');
      notify('success', 'Réponse générée via FAISS');
    } catch (error) {
      notify('error', (error as Error).message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <section className="card">
      <h2>2️⃣ Gestion des connaissances</h2>
      <p>Importer des documents pour enrichir l'index FAISS.</p>
      <form onSubmit={handleUpload} className="form-grid">
        <label>
          Catégorie
          <select name="category">
            <option value="faq">FAQ / Assistance</option>
            <option value="offres">Offres commerciales</option>
            <option value="orange_money">Orange Money</option>
            <option value="energie">Orange Énergie</option>
            <option value="technique">Technique</option>
            <option value="general">Autre</option>
          </select>
        </label>
        <label>
          Fichier
          <input type="file" name="file" required />
        </label>
        <button className="btn primary" type="submit">
          📥 Importer et indexer
        </button>
        <div className="status-pill" style={{ background: 'rgba(148,148,148,0.15)' }}>
          {status || 'Prêt'}
        </div>
      </form>

      <div className="form-grid" style={{ marginTop: 24 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <h3>Documents ({documents.length})</h3>
            <input type="search" placeholder="Filtrer..." value={filter} onChange={handleFilterChange} />
          </div>
          <div className="list-scroll">
            {isLoading && <p>Chargement...</p>}
            {!isLoading &&
              filteredDocs.map((doc) => (
                <div key={doc.id} className="log-entry">
                  <strong>{overrides[doc.id]?.title || doc.original_name}</strong>
                  <br />
                  <small>
                    Catégorie: {doc.category} • {doc.segments} segments • {doc.size_mb} MB
                  </small>
                  <textarea
                    placeholder="Notes / contexte interne"
                    value={overrides[doc.id]?.notes || ''}
                    onChange={(event) => updateOverride(doc.id, 'notes', event.target.value)}
                    style={{ marginTop: 8 }}
                  />
                  <input
                    type="text"
                    placeholder="Titre personnalisé"
                    value={overrides[doc.id]?.title || ''}
                    onChange={(event) => updateOverride(doc.id, 'title', event.target.value)}
                    style={{ marginTop: 8 }}
                  />
                  <div style={{ marginTop: 8, display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button className="btn" type="button" onClick={() => handleSelect(doc.id)}>
                      Aperçu
                    </button>
                    <button className="btn" type="button" onClick={() => handleReindex(doc.id)}>
                      Ré-indexer
                    </button>
                    <button className="btn danger" type="button" onClick={() => handleDelete(doc.id)}>
                      Supprimer
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
        <div>
          <h3>Segments</h3>
          <div className="list-scroll">
            {segments.length === 0 && <p>Sélectionnez un document.</p>}
            {segments.map((segment) => (
              <div key={`${selectedDoc}-${segment.order}`} className="log-entry">
                {segment.text}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ background: 'transparent', border: '1px dashed var(--border)' }}>
        <h3>Tester la pertinence (FAISS)</h3>
        <p>Posez une question pour vérifier la réponse renvoyée par le moteur RAG.</p>
        <textarea value={testQuestion} onChange={(event) => setTestQuestion(event.target.value)} />
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn primary" type="button" onClick={testFaiss} disabled={testing}>
            {testing ? 'Recherche...' : 'Interroger l’index'}
          </button>
          <button className="btn" type="button" onClick={() => setTestQuestion('')}>
            Effacer
          </button>
        </div>
        {testAnswer && (
          <div className="log-entry" style={{ marginTop: 12 }}>
            <strong>Réponse :</strong>
            <br />
            {testAnswer}
          </div>
        )}
      </div>
    </section>
  );
};

export default FAQManager;
