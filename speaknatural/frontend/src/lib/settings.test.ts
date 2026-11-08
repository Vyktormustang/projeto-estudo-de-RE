import { describe, expect, it } from 'vitest';
import { extensionFor } from './api';
import { isValidServerUrl, joinUrl, normalizeServerUrl } from './settings';

describe('normalizeServerUrl', () => {
  it('aceita IP com porta', () => {
    expect(normalizeServerUrl('192.168.0.15:8000')).toBe('http://192.168.0.15:8000');
  });

  it('mantém o esquema informado', () => {
    expect(normalizeServerUrl('http://192.168.0.15:8000')).toBe('http://192.168.0.15:8000');
    expect(normalizeServerUrl('https://meu-pc:9000')).toBe('https://meu-pc:9000');
  });

  it('usa a porta 8000 quando não informada', () => {
    expect(normalizeServerUrl('http://192.168.0.15')).toBe('http://192.168.0.15:8000');
    expect(normalizeServerUrl('localhost')).toBe('http://localhost:8000');
  });

  it('remove barra final', () => {
    expect(normalizeServerUrl('http://192.168.0.15:8000/')).toBe('http://192.168.0.15:8000');
  });

  it('devolve vazio para entrada vazia', () => {
    expect(normalizeServerUrl('   ')).toBe('');
  });
});

describe('isValidServerUrl', () => {
  it('valida endereços plausíveis', () => {
    expect(isValidServerUrl('192.168.0.15:8000')).toBe(true);
    expect(isValidServerUrl('http://meu-pc:8000')).toBe(true);
  });

  it('rejeita lixo', () => {
    expect(isValidServerUrl('')).toBe(false);
    expect(isValidServerUrl('http://')).toBe(false);
  });
});

describe('joinUrl', () => {
  it('usa caminho relativo quando não há base (mesma origem)', () => {
    expect(joinUrl('', '/health')).toBe('/health');
  });

  it('junta base e caminho sem duplicar barra', () => {
    expect(joinUrl('http://192.168.0.15:8000', '/health')).toBe('http://192.168.0.15:8000/health');
    expect(joinUrl('http://192.168.0.15:8000/', 'health')).toBe('http://192.168.0.15:8000/health');
  });
});

describe('extensionFor', () => {
  it('escolhe a extensão pelo tipo MIME', () => {
    expect(extensionFor('audio/webm;codecs=opus')).toBe('webm');
    expect(extensionFor('audio/ogg;codecs=opus')).toBe('ogg');
    expect(extensionFor('audio/mp4')).toBe('m4a');
    expect(extensionFor('audio/wav')).toBe('wav');
    expect(extensionFor('')).toBe('webm');
  });
});
