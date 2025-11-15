import { FC, useMemo } from 'react';

interface DashboardProps {
  cpu?: number;
  ram?: number;
  requestsToday?: number;
  totalRequests?: number;
  perEndpoint?: Record<string, number>;
}

const Dashboard: FC<DashboardProps> = ({
  cpu,
  ram,
  requestsToday,
  totalRequests,
  perEndpoint = {}
}) => {
  const entries = useMemo(() => Object.entries(perEndpoint), [perEndpoint]);

  return (
    <section className="card">
      <h2>1️⃣ Tableau de bord</h2>
      <div className="stat-grid">
        <ProgressStat label="CPU" value={cpu} unit="%" />
        <ProgressStat label="RAM" value={ram} unit="%" />
        <NumberStat label="Requêtes aujourd'hui" value={requestsToday} />
        <NumberStat label="Total requêtes" value={totalRequests} />
      </div>
      {entries.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <h3>Répartition par endpoint</h3>
          <div className="endpoint-grid">
            {entries.map(([endpoint, count]) => (
              <div key={endpoint} className="endpoint-card">
                <div className="endpoint-label">{endpoint}</div>
                <div className="endpoint-bar">
                  <div
                    style={{
                      width: `${Math.min(100, count)}%`,
                      background: 'var(--orange)',
                      height: '100%',
                      borderRadius: 8
                    }}
                  />
                </div>
                <small>{count} appels</small>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

const ProgressStat = ({
  label,
  value,
  unit
}: {
  label: string;
  value?: number;
  unit?: string;
}) => (
  <div className="stat-card">
    <span>{label}</span>
    <strong>{value ?? '--'}{value !== undefined ? unit : ''}</strong>
    {value !== undefined && (
      <div className="progress-bar">
        <div style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    )}
  </div>
);

const NumberStat = ({ label, value }: { label: string; value?: number }) => (
  <div className="stat-card">
    <span>{label}</span>
    <strong>{value ?? '--'}</strong>
  </div>
);

export default Dashboard;
