/**
 * Tipos espelhando a API (backend/app/schemas.py).
 * Se mudar algo no backend, atualize aqui também.
 */

export type Level = 'easy' | 'medium' | 'hard';
export type WordColor = 'green' | 'yellow' | 'red';

export interface Sentence {
  id: string;
  text: string;
  level: Level;
  focus: string;
  tags: string[];
  word_count: number;
}

export interface SentenceList {
  level: Level | null;
  total: number;
  sentences: Sentence[];
}

export interface PhonemeDetail {
  expected: string | null;
  heard: string | null;
  score: number;
  tip: string;
}

export interface WordScore {
  text: string;
  normalized: string;
  score: number;
  color: WordColor;
  presence: number;
  phonemes: PhonemeDetail[];
  tip: string;
}

export interface AnalyzeResponse {
  attempt_id: number;
  sentence_id: string;
  sentence_text: string;
  level: Level;
  transcript: string;
  overall_score: number;
  overall_color: WordColor;
  words: WordScore[];
  duration_seconds: number;
  created_at: string;
  warnings: string[];
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  version: string;
  database: string;
  ffmpeg: boolean;
  whisper: string;
  phonemes: string;
  fake_models: boolean;
  messages: string[];
  server_time: string;
}

export interface AttemptSummary {
  id: number;
  sentence_id: string;
  sentence_text: string;
  level: string;
  overall_score: number;
  created_at: string;
}

export interface HardWord {
  normalized: string;
  display: string;
  level: string;
  attempts: number;
  average_score: number;
  best_score: number;
  last_score: number;
}

export interface HistoryResponse {
  total_attempts: number;
  average_score: number;
  best_score: number;
  streak_days: number;
  attempts: AttemptSummary[];
  hard_words: HardWord[];
}

export const LEVEL_LABEL: Record<Level, string> = {
  easy: 'Fácil',
  medium: 'Médio',
  hard: 'Difícil',
};
