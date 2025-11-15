import { FC, useMemo, useState } from 'react';
import { useFilters } from '../context/Filters';

interface LogEntry {
  timestamp: string;
  message: string;
  scope: string;
}

interface ChatHistoryProps {
  logs: LogEntry[];
  totalRequests?: number;
  requestsToday?: number;
}

const ChatHistory: FC<ChatHistoryProps> = ({ logs, requestsToday, totalRequests }) => {
  const { user } = useFilters();
  const [moduleFilter, setModuleFilter] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const filteredLogs = useMemo(() => {
    return logs.filter((entry) => {
      const ts = new Date(entry.timestamp).getTime();
      const matchesModule = moduleFilter === 'all' || entry.scope === moduleFilter;
      const matchesUser = user === 'all' || entry.message.toLowerCase().includes(user.toLowerCase());
      const matchesStart = !startDate || ts >= new Date(startDate).getTime();
      const matchesEnd = !endDate || ts <= new Date(endDate).getTime();
      return matchesModule && matchesUser && matchesStart && matchesEnd;
    });
  }, [logs, moduleFilter, user, startDate, endDate]);

  const uniqueModules = Array.from(new Set(logs.map((log) => log.scope)));

  return (
    <section className="card">
      <h2>Journal des actions</h2>
      <p>
        Requêtes aujourd'hui: <strong>{requestsToday ?? '--'}</strong> • Total: <strong>{totalRequests ?? '--'}</strong>
      </p>

      <div className="form-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', marginBottom: 16 }}>
        <label>
          Module
          <select value={moduleFilter} onChange={(event) => setModuleFilter(event.target.value)}>
            <option value="all">Tous</option>
            {uniqueModules.map((module) => (
              <option key={module} value={module}>
                {module}
              </option>
            ))}
          </select>
        </label>
        <label>
          Du
          <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
        </label>
        <label>
          Au
          <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </label>
      </div>

      <div className="list-scroll">
        {filteredLogs.length === 0 && <p>Aucune action récente.</p>}
        {filteredLogs.map((entry, index) => (
          <div key={`${entry.timestamp}-${index}`} className="log-entry">
            <strong>{entry.scope}</strong> — {new Date(entry.timestamp).toLocaleTimeString()}
            <br />
            {entry.message}
          </div>
        ))}
      </div>
    </section>
  );
};

export default ChatHistory;
