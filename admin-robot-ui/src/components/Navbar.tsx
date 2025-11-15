import { FC } from 'react';

interface NavbarProps {
  status: 'online' | 'offline';
  onRefresh: () => void;
  lastUpdated?: string;
  activeModule: string;
  onNavigate: (id: string) => void;
}

const navModules = [
  { id: 'faq', label: 'FAQ' },
  { id: 'voice', label: 'Voix' },
  { id: 'greetings', label: 'Salutations' },
  { id: 'settings', label: 'Paramètres' },
  { id: 'history', label: 'Historique' }
];

const Navbar: FC<NavbarProps> = ({ status, onRefresh, lastUpdated, activeModule, onNavigate }) => {
  const label = status === 'online' ? 'Robot en ligne' : 'Hors ligne';

  return (
    <header className="navbar">
      <div>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Admin Robot Orange Faso</h1>
        <p style={{ margin: 0, color: 'var(--muted)' }}>Console de supervision RAG + Audio + Réseau</p>
        <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {navModules.map((module) => (
            <button
              key={module.id}
              className={module.id === activeModule ? 'btn primary' : 'btn'}
              type="button"
              onClick={() => onNavigate(module.id)}
            >
              {module.label}
            </button>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span className={`status-pill ${status}`}>{label}</span>
          {lastUpdated && <small style={{ color: 'var(--muted)' }}>Maj: {lastUpdated}</small>}
          <button className="btn primary" onClick={onRefresh}>
            Rafraîchir
          </button>
      </div>
    </header>
  );
};

export default Navbar;
