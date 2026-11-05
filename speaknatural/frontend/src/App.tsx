import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from './lib/api';
import { getThemeChoice, setThemeChoice } from './lib/settings';
import type { ThemeChoice } from './lib/settings';
import { HistoryTab } from './components/HistoryTab';
import { PracticeTab } from './components/PracticeTab';
import { SettingsTab } from './components/SettingsTab';
import { HistoryIcon, MoonIcon, PracticeIcon, SettingsIcon, SunIcon } from './components/Icons';

type Tab = 'practice' | 'history' | 'settings';
type Connection = 'checking' | 'online' | 'offline' | 'degraded';

const TABS: { id: Tab; label: string; icon: (props: { size?: number }) => JSX.Element }[] = [
  { id: 'practice', label: 'Praticar', icon: PracticeIcon },
  { id: 'history', label: 'Histórico', icon: HistoryIcon },
  { id: 'settings', label: 'Servidor', icon: SettingsIcon },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('practice');
  const [connection, setConnection] = useState<Connection>('checking');
  const [theme, setTheme] = useState<ThemeChoice>(() => getThemeChoice());

  const checkConnection = useCallback(async () => {
    setConnection('checking');
    try {
      const health = await api.health();
      setConnection(health.status === 'ok' ? 'online' : 'degraded');
    } catch (error) {
      setConnection('offline');
      if (!(error instanceof ApiError)) {
        // falha inesperada: mantém offline, mas não quebra a tela
        console.warn(error);
      }
    }
  }, []);

  useEffect(() => {
    void checkConnection();
    const interval = window.setInterval(() => void checkConnection(), 60_000);
    return () => window.clearInterval(interval);
  }, [checkConnection]);

  const toggleTheme = () => {
    const next: ThemeChoice = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    setThemeChoice(next);
  };

  const connectionLabel: Record<Connection, string> = {
    checking: 'Verificando servidor...',
    online: 'Servidor conectado',
    offline: 'Servidor offline',
    degraded: 'Servidor com avisos',
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__brand">
          <span className="app-header__logo" aria-hidden="true">
            SN
          </span>
          <div>
            <h1>SpeakNatural</h1>
            <p className="app-header__tagline">Fale inglês como um nativo</p>
          </div>
        </div>
        <div className="app-header__actions">
          <button
            type="button"
            className="connection"
            onClick={() => void checkConnection()}
            title={connectionLabel[connection]}
            aria-label={connectionLabel[connection]}
          >
            <span className={`connection__dot connection__dot--${connection}`} />
            <span className="connection__text">{connectionLabel[connection]}</span>
          </button>
          <button type="button" className="icon-button" onClick={toggleTheme} aria-label="Trocar tema">
            {theme === 'dark' ? <SunIcon size={20} /> : <MoonIcon size={20} />}
          </button>
        </div>
      </header>

      <main className="app-main">
        {tab === 'practice' ? (
          <PracticeTab onOpenSettings={() => setTab('settings')} />
        ) : null}
        {tab === 'history' ? <HistoryTab active={tab === 'history'} onGoToPractice={() => setTab('practice')} /> : null}
        {tab === 'settings' ? <SettingsTab /> : null}
      </main>

      <nav className="tab-bar" aria-label="Navegação principal">
        {TABS.map((item) => {
          const Icon = item.icon;
          const active = tab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`tab-bar__item ${active ? 'tab-bar__item--active' : ''}`}
              onClick={() => setTab(item.id)}
              aria-current={active ? 'page' : undefined}
            >
              <Icon size={24} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
