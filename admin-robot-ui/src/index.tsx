import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/main.css';
import './styles/livechat.css';
import './registerSW';
import { NotificationProvider } from './context/Notifications';
import Notifications from './components/Notifications';
import { FilterProvider } from './context/Filters';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <NotificationProvider>
      <FilterProvider>
        <Notifications />
        <App />
      </FilterProvider>
    </NotificationProvider>
  </React.StrictMode>
);
