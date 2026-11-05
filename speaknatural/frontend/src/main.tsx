import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { applyTheme, getThemeChoice } from './lib/settings';
import './styles.css';

// Aplica claro/escuro antes de desenhar (evita "piscar" branco).
applyTheme(getThemeChoice());

const container = document.getElementById('root');
if (!container) {
  throw new Error('Elemento #root não encontrado no index.html');
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
