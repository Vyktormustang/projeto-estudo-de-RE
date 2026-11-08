import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../lib/api';
import {
  DEFAULT_SERVER_URL,
  getServerUrl,
  getThemeChoice,
  isNativeApp,
  isValidServerUrl,
  normalizeServerUrl,
  setServerUrl,
  setThemeChoice,
} from '../lib/settings';
import type { ThemeChoice } from '../lib/settings';
import type { HealthResponse } from '../lib/types';
import { Banner } from './Banner';
import { CheckIcon, MoonIcon, SunIcon } from './Icons';

type TestState =
  | { kind: 'idle' }
  | { kind: 'testing' }
  | { kind: 'success'; health: HealthResponse; url: string }
  | { kind: 'failure'; message: string };

const THEME_OPTIONS: { value: ThemeChoice; label: string }[] = [
  { value: 'auto', label: 'Automático' },
  { value: 'light', label: 'Claro' },
  { value: 'dark', label: 'Escuro' },
];

/** Tela "Servidor": endereço do PC, teste de conexão, tema e informações. */
export function SettingsTab() {
  const native = isNativeApp();
  const savedUrl = getServerUrl();
  const [input, setInput] = useState(savedUrl || (native ? DEFAULT_SERVER_URL : ''));
  const [test, setTest] = useState<TestState>({ kind: 'idle' });
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [theme, setTheme] = useState<ThemeChoice>(() => getThemeChoice());

  const runTest = useCallback(async (url: string) => {
    setTest({ kind: 'testing' });
    try {
      const health = await api.healthAt(url);
      setTest({ kind: 'success', health, url });
      return health;
    } catch (error) {
      setTest({
        kind: 'failure',
        message: error instanceof ApiError ? error.message : 'Não consegui conectar a esse endereço.',
      });
      return null;
    }
  }, []);

  useEffect(() => {
    // Ao abrir a tela, já testamos o endereço salvo (feedback imediato).
    void runTest(getServerUrl());
  }, [runTest]);

  const save = async () => {
    const normalized = normalizeServerUrl(input);
    if (!normalized || !isValidServerUrl(input)) {
      setSaveMessage('Endereço inválido. Use o formato http://192.168.0.15:8000');
      return;
    }
    setServerUrl(normalized);
    setInput(normalized);
    setSaveMessage('Endereço salvo neste aparelho.');
    await runTest(normalized);
  };

  const useCurrentOrigin = () => {
    const origin = window.location.origin;
    setInput(origin);
    setSaveMessage('Endereço preenchido com o deste navegador. Toque em “Salvar”.');
  };

  const changeTheme = (choice: ThemeChoice) => {
    setTheme(choice);
    setThemeChoice(choice);
  };

  return (
    <div className="settings">
      <section className="card">
        <h2 className="card__title">Servidor</h2>
        <p className="muted small">
          O servidor roda no seu computador (Python). O celular precisa estar no mesmo Wi‑Fi e usar o IP do
          PC, por exemplo <code>http://192.168.0.15:8000</code>.
        </p>

        <label className="field">
          <span className="field__label">Endereço do servidor</span>
          <input
            className="field__input"
            type="url"
            inputMode="url"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            placeholder={DEFAULT_SERVER_URL}
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />
        </label>

        <div className="settings__actions">
          <button type="button" className="button button--primary" onClick={() => void save()}>
            <CheckIcon size={20} /> Salvar endereço
          </button>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => void runTest(normalizeServerUrl(input) || getServerUrl())}
            disabled={test.kind === 'testing'}
          >
            {test.kind === 'testing' ? 'Testando...' : 'Testar conexão'}
          </button>
        </div>

        {!native ? (
          <button type="button" className="link-button" onClick={useCurrentOrigin}>
            Usar o endereço deste navegador
          </button>
        ) : null}

        {saveMessage ? <p className="muted small">{saveMessage}</p> : null}

        {test.kind === 'success' ? (
          <Banner tone={test.health.status === 'ok' ? 'success' : 'warning'} title="Conectado!">
            <span className="banner__list">
              <span>
                Servidor {test.health.version} · {test.url || 'mesma origem'}
              </span>
              <span>ffmpeg: {test.health.ffmpeg ? 'instalado' : 'FALTANDO (instale no PC)'}</span>
              <span>Transcrição: {test.health.whisper}</span>
              <span>Sons: {test.health.phonemes}</span>
              {test.health.fake_models ? <span>Modo demonstração ativo (notas simuladas)</span> : null}
              {test.health.messages.map((message) => (
                <span key={message}>⚠ {message}</span>
              ))}
            </span>
          </Banner>
        ) : null}

        {test.kind === 'failure' ? (
          <Banner tone="error" title="Sem conexão">{test.message}</Banner>
        ) : null}
      </section>

      <section className="card">
        <h2 className="card__title">Aparência</h2>
        <div className="theme-selector">
          {THEME_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`chip ${theme === option.value ? 'chip--active' : ''}`}
              onClick={() => changeTheme(option.value)}
              aria-pressed={theme === option.value}
            >
              {option.value === 'light' ? <SunIcon size={18} /> : null}
              {option.value === 'dark' ? <MoonIcon size={18} /> : null}
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <h2 className="card__title">Como conseguir o IP do PC</h2>
        <ol className="steps">
          <li>
            <strong>Windows:</strong> abra o Prompt de Comando e digite <code>ipconfig</code>. O número em
            “Endereço IPv4” (ex.: 192.168.0.15) é o que você precisa.
          </li>
          <li>
            <strong>Mac/Linux:</strong> digite <code>ifconfig</code> ou <code>ip addr</code> e procure o
            endereço 192.168.x.x.
          </li>
          <li>
            No app, escreva <code>http://</code> + esse número + <code>:8000</code> e toque em “Salvar
            endereço”.
          </li>
          <li>
            No PC, o servidor precisa estar rodando com <code>start-server</code> (a janela preta do Python
            fica aberta).
          </li>
        </ol>
        <p className="muted tiny">
          Firewall do Windows: na primeira vez, permita o Python na rede privada. Se o teste falhar, veja
          “Problemas comuns” no README.
        </p>
      </section>

      <section className="card">
        <h2 className="card__title">Sobre</h2>
        <p className="muted small">
          SpeakNatural · treino de pronúncia do inglês com análise por palavra e por som. Roda 100% no seu
          computador, com modelos open source (faster-whisper + wav2vec2). Nenhuma conta, nenhuma chave de
          API, nenhum áudio sai da sua rede.
        </p>
      </section>
    </div>
  );
}
