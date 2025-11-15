import { useEffect, useMemo, useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import FAQManager from './components/FAQManager';
import VoiceTester from './components/VoiceTester';
import UserGreetings from './components/UserGreetings';
import Settings from './components/Settings';
import ChatHistory from './components/ChatHistory';
import Dashboard from './components/Dashboard';
import LiveChat from './components/LiveChat';
import { api } from './services/api';

interface MetricsResponse {
  requests: {
    total_requests: number;
    requests_today: number;
    logs: { timestamp: string; message: string; scope: string }[];
    per_endpoint?: Record<string, number>;
  };
  cpu_percent?: number;
}

const App = () => {
  const [activeModule, setActiveModule] = useState('faq');
  const [health, setHealth] = useState<'online' | 'offline'>('offline');
  const [stats, setStats] = useState<{ cpu_percent?: number; ram_percent?: number } | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const loadDashboard = async () => {
    try {
      const [healthData, statsData, metricsData] = await Promise.all([
        api.getHealth(),
        api.getStats(),
        api.getMetrics()
      ]);
      setHealth(healthData.status === 'ok' ? 'online' : 'offline');
      setStats({ cpu_percent: statsData.cpu_percent, ram_percent: statsData.ram_percent });
      setMetrics(metricsData);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadDashboard();
    const timer = setInterval(loadDashboard, 20000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="app-layout">
      <Sidebar active={activeModule} onSelect={setActiveModule} />
      <div>
        <Navbar
          status={health}
          onRefresh={loadDashboard}
          lastUpdated={lastUpdate}
          activeModule={activeModule}
          onNavigate={setActiveModule}
        />
        <div className="main-content">
          {metrics && (
            <Dashboard
              cpu={stats?.cpu_percent}
              ram={stats?.ram_percent}
              requestsToday={metrics.requests.requests_today}
              totalRequests={metrics.requests.total_requests}
              perEndpoint={metrics.requests.per_endpoint}
            />
          )}
          {activeModule === 'faq' && <FAQManager />}
          {activeModule === 'voice' && <VoiceTester />}
          {activeModule === 'live' && <LiveChat />}
          {activeModule === 'greetings' && <UserGreetings />}
          {activeModule === 'settings' && <Settings />}
          {activeModule === 'history' && (
            <ChatHistory
              logs={metrics?.requests.logs || []}
              requestsToday={metrics?.requests.requests_today}
              totalRequests={metrics?.requests.total_requests}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
