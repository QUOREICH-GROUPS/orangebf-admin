import { ChangeEvent, FC } from 'react';
import { useFilters } from '../context/Filters';

const modules = [
  { id: 'faq', label: 'Gestion FAQ / RAG' },
  { id: 'voice', label: 'Test Voix & RAG' },
  { id: 'live', label: 'Live Conversation' },
  { id: 'greetings', label: 'Audios & Salutations' },
  { id: 'settings', label: 'Paramètres' },
  { id: 'history', label: 'Journal des actions' }
];

interface SidebarProps {
  active: string;
  onSelect: (id: string) => void;
}

const Sidebar: FC<SidebarProps> = ({ active, onSelect }) => {
  const { category, language, user, setCategory, setLanguage, setUser } = useFilters();

  const handleUserChange = (event: ChangeEvent<HTMLInputElement>) => setUser(event.target.value);

  return (
    <aside className="sidebar">
      <nav>
        {modules.map((item) => (
          <button
            key={item.id}
            className={item.id === active ? 'active' : ''}
            onClick={() => onSelect(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div style={{ marginTop: 24 }}>
        <h4>Filtres rapides</h4>
        <label>
          Catégorie
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="all">Toutes</option>
            <option value="faq">FAQ</option>
            <option value="offres">Offres</option>
            <option value="orange_money">Orange Money</option>
            <option value="energie">Énergie</option>
            <option value="technique">Technique</option>
          </select>
        </label>
        <label>
          Langue
          <select value={language} onChange={(event) => setLanguage(event.target.value as any)}>
            <option value="all">Toutes</option>
            <option value="fr">Français</option>
            <option value="moore">Mooré</option>
            <option value="dioula">Dioula</option>
            <option value="fulfulde">Fulfuldé</option>
          </select>
        </label>
        <label>
          Utilisateur
          <input type="text" value={user === 'all' ? '' : user} onChange={handleUserChange} placeholder="Agent ou client" />
        </label>
      </div>
    </aside>
  );
};

export default Sidebar;
