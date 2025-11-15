import { FC } from 'react';
import { useNotifications } from '../context/Notifications';

const typeToClass: Record<string, string> = {
  info: 'toast-info',
  success: 'toast-success',
  error: 'toast-error'
};

const Notifications: FC = () => {
  const { toasts, dismiss } = useNotifications();

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast ${typeToClass[toast.type] || ''}`}>
          <span>{toast.message}</span>
          <button type="button" onClick={() => dismiss(toast.id)}>
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};

export default Notifications;
