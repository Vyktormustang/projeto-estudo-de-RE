import React, { useState } from 'react';
import {
  Award,
  BookOpen,
  Brain,
  CheckCircle2,
  Clock,
  Lightbulb,
  Sparkles,
  X,
  Zap,
} from 'lucide-react';
import {
  getLessonFieldMission,
  getLessonMasteryTier,
  getLessonZeroStep,
  MASTERY_TIERS,
} from '../engine/teachingsCatalog';
import { TeachingLesson, TeachingProgressEntry } from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { triggerHaptic } from '../services/vaultStorage';

interface Props {
  lesson: TeachingLesson;
  existingProgress?: TeachingProgressEntry;
  fieldMissionDone?: boolean;
  startInQuizMode?: boolean;
  onCompleteQuiz: (lesson: TeachingLesson, wasCorrect: boolean) => void;
  onToggleFieldMission?: (lessonId: string) => void;
  onNextLesson?: () => void;
  onClose: () => void;
}

const MASTERY_LABELS: Record<0 | 1 | 2 | 3 | 4, string> = {
  0: 'Em Revisão (1 dia)',
  1: 'Nível 1 • Próxima revisão em 1 dia',
  2: 'Nível 2 • Próxima revisão em 3 dias',
  3: 'Nível 3 • Próxima revisão em 7 dias',
  4: 'Nível 4 • Dominado (Ciclo de 21 dias)',
};

export const TeachingLessonModal: React.FC<Props> = ({
  lesson,
  existingProgress,
  fieldMissionDone = false,
  startInQuizMode = false,
  onCompleteQuiz,
  onToggleFieldMission,
  onNextLesson,
  onClose,
}) => {
  const [step, setStep] = useState<'READ' | 'QUIZ'>(startInQuizMode ? 'QUIZ' : 'READ');
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const tier = getLessonMasteryTier(lesson);
  const tierMeta = MASTERY_TIERS.find((t) => t.tier === tier);
  const zeroStep = getLessonZeroStep(lesson);
  const fieldMission = getLessonFieldMission(lesson);

  const isCorrect = selectedIdx === lesson.correctOptionIndex;

  const handleSelectOption = (idx: number) => {
    if (submitted) return;
    setSelectedIdx(idx);
    setSubmitted(true);
    const ok = idx === lesson.correctOptionIndex;
    if (ok) {
      triggerHaptic('success');
      playTacticalChime('VICTORY');
    } else {
      triggerHaptic('heavy');
    }
    onCompleteQuiz(lesson, ok);
  };

  const previewNextLevel: 0 | 1 | 2 | 3 | 4 = isCorrect
    ? (Math.min(4, Math.max(1, (existingProgress?.masteryLevel ?? 0) + 1)) as 1 | 2 | 3 | 4)
    : 0;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="section-header" style={{ marginBottom: 10 }}>
          <div>
            <div className="section-kicker">{lesson.trackTitle}</div>
            <h2 className="section-title" style={{ fontSize: 17.5 }}>
              {lesson.title}
            </h2>
          </div>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ minHeight: 36, padding: '6px 10px', flexShrink: 0 }}
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <div className="chip-row" style={{ marginBottom: 14 }}>
          {tierMeta && <span className="badge badge-cyan">{tierMeta.badgeLabel}</span>}
          <span className="badge badge-yellow">
            <Sparkles size={11} /> {lesson.mentorName}
          </span>
          <span className="badge badge-cyan">
            <Clock size={11} /> ~{lesson.readTimeSec}s
          </span>
          {existingProgress && existingProgress.masteryLevel > 0 && (
            <span className="badge badge-green">
              Maestria {existingProgress.masteryLevel}/4
            </span>
          )}
        </div>

        {step === 'READ' ? (
          <div>
            {/* 1. ESSENCIA CLARA */}
            <div
              style={{
                padding: 14,
                borderRadius: 14,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  fontSize: 11.5,
                  fontWeight: 800,
                  color: '#fbbf24',
                  textTransform: 'uppercase',
                  marginBottom: 5,
                }}
              >
                <BookOpen size={13} style={{ verticalAlign: 'middle' }} /> A Lição em Português
                Claro
              </div>
              <div style={{ fontSize: 14.3, lineHeight: 1.6 }}>{lesson.coreEssence}</div>
            </div>

            {/* 2. MECANISMO CIENTIFICO (ELABORATIVE INTERROGATION) */}
            <div
              style={{
                padding: 13,
                borderRadius: 14,
                background: 'var(--cyan-soft)',
                border: '1px solid rgba(6,182,212,0.32)',
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  fontSize: 11.5,
                  fontWeight: 800,
                  color: '#22d3ee',
                  textTransform: 'uppercase',
                  marginBottom: 4,
                }}
              >
                <Brain size={13} style={{ verticalAlign: 'middle' }} /> Por Que Isso Funciona no
                Cérebro e no Corpo?
              </div>
              <div style={{ fontSize: 13.4, lineHeight: 1.55, color: '#e0f2fe' }}>
                {lesson.whyItWorksMechanism}
              </div>
              <div
                style={{
                  fontSize: 11.3,
                  color: '#7dd3fc',
                  marginTop: 7,
                  fontStyle: 'italic',
                }}
              >
                Base científica: {lesson.scientificSource}
              </div>
            </div>

            {/* 3. DEGRAU ZERO (WORKED EXAMPLE PARA INICIANTE ABSOLUTO) */}
            <div
              style={{
                padding: 13,
                borderRadius: 14,
                background: 'var(--amber-soft)',
                border: '1px solid rgba(245,158,11,0.35)',
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  fontSize: 11.5,
                  fontWeight: 800,
                  color: '#fbbf24',
                  textTransform: 'uppercase',
                  marginBottom: 4,
                }}
              >
                🟢 Degrau Zero — Exemplo Prático Passo a Passo
              </div>
              <div style={{ fontSize: 13.4, lineHeight: 1.52 }}>{zeroStep}</div>
            </div>

            {/* 4. ACAO PRATICA HOJE + MISSAO REAL DE CAMPO */}
            <div
              style={{
                padding: 13,
                borderRadius: 14,
                background: 'var(--emerald-soft)',
                border: '1px solid rgba(16,185,129,0.35)',
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  fontSize: 11.5,
                  fontWeight: 800,
                  color: '#34d399',
                  textTransform: 'uppercase',
                  marginBottom: 4,
                }}
              >
                <Lightbulb size={13} style={{ verticalAlign: 'middle' }} /> Missão Real na Sua Vida
                Hoje
              </div>
              <div style={{ fontSize: 13.5, lineHeight: 1.52, color: '#d1fae5', marginBottom: 8 }}>
                {fieldMission}
              </div>
              {onToggleFieldMission && (
                <button
                  type="button"
                  className={`btn ${fieldMissionDone ? 'btn-emerald' : 'btn-ghost'}`}
                  style={{ minHeight: 34, padding: '5px 11px', fontSize: 12 }}
                  onClick={() => {
                    triggerHaptic('light');
                    onToggleFieldMission(lesson.id);
                  }}
                >
                  <CheckCircle2 size={13} />{' '}
                  {fieldMissionDone
                    ? 'Missão Praticada na Vida Real ✓'
                    : 'Marcar Missão Praticada na Vida Real'}
                </button>
              )}
            </div>

            <button
              type="button"
              className="btn btn-primary btn-block"
              onClick={() => {
                triggerHaptic('light');
                setStep('QUIZ');
              }}
            >
              <Zap size={17} /> Testar na Prática (Gravar na Memória)
            </button>
          </div>
        ) : (
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 10,
              }}
            >
              <span className="section-kicker" style={{ color: 'var(--cyan)' }}>
                Simulador de Decisão Real (Evocação Ativa)
              </span>
              {!submitted && (
                <button
                  type="button"
                  className="chip"
                  style={{ padding: '4px 10px', fontSize: 11.5 }}
                  onClick={() => setStep('READ')}
                >
                  Rever Lição
                </button>
              )}
            </div>

            <div
              style={{
                padding: 13,
                borderRadius: 12,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-strong)',
                fontSize: 14.2,
                fontWeight: 700,
                lineHeight: 1.52,
                marginBottom: 12,
              }}
            >
              {lesson.dilemmaPrompt}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {lesson.dilemmaOptions.map((opt, idx) => {
                let borderCol = 'var(--border-subtle)';
                let bgCol = 'var(--bg-input)';
                if (submitted) {
                  if (idx === lesson.correctOptionIndex) {
                    borderCol = 'var(--emerald)';
                    bgCol = 'var(--emerald-soft)';
                  } else if (idx === selectedIdx) {
                    borderCol = 'var(--crimson)';
                    bgCol = 'var(--crimson-soft)';
                  }
                }
                return (
                  <button
                    key={idx}
                    type="button"
                    disabled={submitted}
                    onClick={() => handleSelectOption(idx)}
                    style={{
                      textAlign: 'left',
                      padding: '12px 13px',
                      borderRadius: 12,
                      border: `1.5px solid ${borderCol}`,
                      background: bgCol,
                      cursor: submitted ? 'default' : 'pointer',
                      fontSize: 13.5,
                      lineHeight: 1.45,
                      display: 'flex',
                      gap: 9,
                      alignItems: 'flex-start',
                    }}
                  >
                    <span
                      className="mono"
                      style={{ color: '#fbbf24', fontWeight: 800, flexShrink: 0 }}
                    >
                      {String.fromCharCode(65 + idx)}.
                    </span>
                    <span>{opt}</span>
                  </button>
                );
              })}
            </div>

            {submitted && (
              <div
                style={{
                  marginTop: 14,
                  padding: 13,
                  borderRadius: 14,
                  background: isCorrect ? 'var(--emerald-soft)' : 'var(--amber-soft)',
                  border: `1px solid ${isCorrect ? 'var(--emerald)' : 'var(--amber)'}`,
                }}
              >
                <div
                  style={{
                    fontWeight: 800,
                    fontSize: 14,
                    color: isCorrect ? '#34d399' : '#fbbf24',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  {isCorrect ? (
                    <>
                      <CheckCircle2 size={16} /> Ensinamento Dominado na Prática!
                    </>
                  ) : (
                    <>
                      <Award size={16} /> Armadilha Identificada — Correção Gravada:
                    </>
                  )}
                </div>

                <div style={{ fontSize: 13.3, lineHeight: 1.52, marginBottom: 8 }}>
                  {isCorrect ? lesson.feedbackCorrect : lesson.feedbackTrap}
                </div>

                <div
                  className="mono"
                  style={{
                    fontSize: 11.5,
                    color: 'var(--text-secondary)',
                    marginBottom: 12,
                  }}
                >
                  📅 Repetição Espaçada: {MASTERY_LABELS[previewNextLevel]}
                </div>

                {onNextLesson ? (
                  <div className="grid-2">
                    <button type="button" className="btn btn-ghost" onClick={onClose}>
                      Concluir
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => {
                        triggerHaptic('light');
                        onNextLesson();
                      }}
                    >
                      Próxima Lição →
                    </button>
                  </div>
                ) : (
                  <button type="button" className="btn btn-primary btn-block" onClick={onClose}>
                    Concluir e Salvar Progresso
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
