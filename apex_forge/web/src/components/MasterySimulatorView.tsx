import React, { useState } from 'react';
import {
  Award,
  BookOpen,
  CheckCircle2,
  Compass,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import {
  applySimulatorChoice,
  createInitialSimulatorRun,
  evaluateFinalMasteryReport,
  SIMULATOR_CHAPTERS,
  SimulatorRunState,
} from '../engine/masterySimulator';
import { getLessonById } from '../engine/teachingsCatalog';
import {
  SimulatorStats,
  TeachingLesson,
  TeachingProgressEntry,
} from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { triggerHaptic } from '../services/vaultStorage';
import { TeachingLessonModal } from './TeachingLessonModal';

interface Props {
  simulatorStats?: SimulatorStats;
  progressMap: Record<string, TeachingProgressEntry>;
  completedFieldMissions?: Record<string, string>;
  onFinishSimulation: (score1000: number, rankTitle: string) => void;
  onCompleteLessonQuiz: (lesson: TeachingLesson, wasCorrect: boolean) => void;
  onToggleFieldMission?: (lessonId: string) => void;
}

export const MasterySimulatorView: React.FC<Props> = ({
  simulatorStats,
  progressMap,
  completedFieldMissions = {},
  onFinishSimulation,
  onCompleteLessonQuiz,
  onToggleFieldMission,
}) => {
  const [runState, setRunState] = useState<SimulatorRunState>(() => createInitialSimulatorRun());
  const [pendingFeedback, setPendingFeedback] = useState<{
    chosenIdx: 0 | 1 | 2 | 3;
    title: string;
    narrative: string;
    isMaster: boolean;
    linkedLessonId: string;
  } | null>(null);
  const [modalLesson, setModalLesson] = useState<TeachingLesson | null>(null);

  const chapter =
    !runState.completed && runState.currentChapterIndex < SIMULATOR_CHAPTERS.length
      ? SIMULATOR_CHAPTERS[runState.currentChapterIndex]
      : null;

  const handleChoose = (idx: 0 | 1 | 2 | 3) => {
    if (!chapter || pendingFeedback) return;
    const opt = chapter.options[idx];
    if (opt.isMasterChoice) {
      triggerHaptic('success');
      playTacticalChime('VICTORY');
    } else {
      triggerHaptic('heavy');
    }

    const updated = applySimulatorChoice(runState, idx);
    setRunState(updated);
    setPendingFeedback({
      chosenIdx: idx,
      title: opt.consequenceTitle,
      narrative: opt.consequenceNarrative,
      isMaster: opt.isMasterChoice,
      linkedLessonId: chapter.linkedLessonId,
    });

    if (updated.completed) {
      const rep = evaluateFinalMasteryReport(updated);
      onFinishSimulation(rep.score1000, rep.rankTitle);
    }
  };

  const resetRun = () => {
    triggerHaptic('light');
    setPendingFeedback(null);
    setRunState(createInitialSimulatorRun());
  };

  const finalReport = runState.completed ? evaluateFinalMasteryReport(runState) : null;

  const attrBars: { label: string; val: number; color: string }[] = [
    { label: 'Caráter, Sabedoria Bíblica & Serviço', val: runState.attributes.carater, color: '#fbbf24' },
    { label: 'Corpo & Energia', val: runState.attributes.vigor, color: '#10b981' },
    { label: 'Máquina de Aprender', val: runState.attributes.aprendizado, color: '#06b6d4' },
    { label: 'Domínio Próprio & Emoção', val: runState.attributes.autogoverno, color: '#f59e0b' },
    { label: 'Palavra, Língua & Social', val: runState.attributes.retorica, color: '#a78bfa' },
    { label: 'Lógica, Mordomia & Recursos', val: runState.attributes.estrategia, color: '#38bdf8' },
  ];

  return (
    <>
      {modalLesson && (
        <TeachingLessonModal
          key={modalLesson.id}
          lesson={modalLesson}
          existingProgress={progressMap[modalLesson.id]}
          fieldMissionDone={Boolean(completedFieldMissions[modalLesson.id])}
          onCompleteQuiz={onCompleteLessonQuiz}
          onToggleFieldMission={onToggleFieldMission}
          onClose={() => setModalLesson(null)}
        />
      )}

      {/* CABECALHO & TELEMETRIA VIVA DO JOVEM DO ZERO AO MESTRE */}
      <div className="card card-amber">
        <div className="section-header">
          <div>
            <div className="section-kicker">
              Simulador Interativo • {SIMULATOR_CHAPTERS.length} Capítulos Decisivos da Vida &amp; do Caráter
            </div>
            <h2 className="section-title">Jornada: Do Jovem Sem Habilidades ao Mestre</h2>
          </div>
          <Compass size={23} color="var(--amber)" />
        </div>

        <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
          Você começa no <strong>Marco Zero (10/100 em todas as áreas)</strong>: sem preparo físico,
          sem método de estudo, tímido, procrastinando e sem reserva financeira. Percorra os{' '}
          <strong>{SIMULATOR_CHAPTERS.length} crisóis da vida real</strong> — da saída da inércia até o teste supremo de
          perdão, governança na fartura, foco na muralha e liderança servidora ensinado por{' '}
          <strong>Jesus Cristo</strong>!
        </p>

        {simulatorStats && simulatorStats.completedRuns > 0 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
              padding: '8px 11px',
              borderRadius: 10,
              background: 'var(--bg-elevated)',
              fontSize: 12.2,
            }}
          >
            <span>
              <Award size={13} color="var(--amber)" style={{ verticalAlign: 'middle' }} /> Recorde:{' '}
              <strong>{simulatorStats.bestScore}/1000 pts</strong>
            </span>
            <span className="muted">{simulatorStats.completedRuns}x concluído</span>
          </div>
        )}

        {/* 5 BARRAS DE ATRIBUTOS DA BASE ABSOLUTA */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {attrBars.map((b) => (
            <div key={b.label}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 11.8,
                  fontWeight: 700,
                  marginBottom: 3,
                }}
              >
                <span>{b.label}</span>
                <span className="mono" style={{ color: b.color }}>
                  {b.val}/100
                </span>
              </div>
              <div className="progress-track" style={{ height: 7 }}>
                <div
                  style={{
                    height: '100%',
                    width: `${b.val}%`,
                    background: b.color,
                    borderRadius: 999,
                    transition: 'width 0.35s ease',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* FEEDBACK CAUSAL IMEDIATO DEPOIS DA DECISAO */}
      {pendingFeedback && (
        <div
          className="card"
          style={{
            border: pendingFeedback.isMaster
              ? '1.5px solid var(--emerald)'
              : '1.5px solid var(--crimson)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontWeight: 800,
              fontSize: 15,
              color: pendingFeedback.isMaster ? '#34d399' : '#fca5a5',
              marginBottom: 6,
            }}
          >
            {pendingFeedback.isMaster ? <CheckCircle2 size={18} /> : <ShieldAlert size={18} />}
            {pendingFeedback.isMaster
              ? `Decisão de Mestre: ${pendingFeedback.title}`
              : `Armadilha Real: ${pendingFeedback.title}`}
          </div>

          <p style={{ margin: '0 0 12px', fontSize: 13.6, lineHeight: 1.56 }}>
            {pendingFeedback.narrative}
          </p>

          <div className="grid-2">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                const les = getLessonById(pendingFeedback.linkedLessonId);
                if (les) setModalLesson(les);
              }}
            >
              <BookOpen size={15} /> Ver Lição Científica
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                triggerHaptic('light');
                setPendingFeedback(null);
              }}
            >
              {runState.completed ? 'Ver Diagnóstico Final →' : 'Avançar na Jornada →'}
            </button>
          </div>
        </div>
      )}

      {/* CAPITULO ATUAL (SE AINDA NAO AGUARDANDO FEEDBACK E NAO CONCLUIDO) */}
      {!pendingFeedback && chapter && (
        <div className="card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 8,
            }}
          >
            <span className="badge badge-cyan">
              Capítulo {chapter.chapterNumber}/{SIMULATOR_CHAPTERS.length} •{' '}
              {chapter.timeHorizonLabel}
            </span>
            {chapter.chapterNumber > 1 && (
              <button
                type="button"
                className="chip"
                style={{ padding: '3px 9px', fontSize: 11 }}
                onClick={resetRun}
              >
                <RotateCcw size={11} /> Reiniciar
              </button>
            )}
          </div>

          <h3 className="section-title" style={{ fontSize: 17.5, marginBottom: 8 }}>
            {chapter.title}
          </h3>

          <div
            style={{
              padding: 13,
              borderRadius: 12,
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              fontSize: 14,
              lineHeight: 1.58,
              marginBottom: 10,
            }}
          >
            {chapter.scenarioContext}
          </div>

          <div className="muted" style={{ fontSize: 11.6, marginBottom: 12 }}>
            <Sparkles size={11} color="var(--amber)" style={{ verticalAlign: 'middle' }} /> Princípio
            em jogo: <em>{chapter.scientificAnchor}</em>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
            {chapter.options.map((opt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleChoose(idx as 0 | 1 | 2 | 3)}
                style={{
                  textAlign: 'left',
                  padding: '12px 13px',
                  borderRadius: 12,
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: 13.4,
                  lineHeight: 1.48,
                  cursor: 'pointer',
                }}
              >
                <strong style={{ color: 'var(--amber)' }}>
                  {String.fromCharCode(65 + idx)}.
                </strong>{' '}
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* RELATORIO DIAGNOSTICO FINAL APOS OS 8 CAPITULOS */}
      {!pendingFeedback && finalReport && (
        <div className="card card-emerald">
          <div className="section-kicker">Resultado da Sua Jornada do Zero ao Mestre</div>
          <h3 className="section-title" style={{ fontSize: 18, marginTop: 2 }}>
            {finalReport.rankTitle}
          </h3>

          <div className="grid-2" style={{ margin: '12px 0' }}>
            <div className="metric-box">
              <div className="metric-label">Pontuação Polímata</div>
              <div className="metric-value">{finalReport.score1000}/1000</div>
              <div className="metric-sub">Índice da Base Absoluta</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Escolhas de Mestre</div>
              <div className="metric-value">
                {finalReport.masterDecisionsCount}/{finalReport.totalChapters}
              </div>
              <div className="metric-sub">Crisóis vencidos</div>
            </div>
          </div>

          <p style={{ fontSize: 13.6, lineHeight: 1.55, marginTop: 0 }}>
            {finalReport.rankSummary}
          </p>

          <div
            style={{
              padding: 12,
              borderRadius: 12,
              background: 'var(--bg-elevated)',
              marginBottom: 12,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 800, color: '#fbbf24', marginBottom: 6 }}>
              <TrendingUp size={13} style={{ verticalAlign: 'middle' }} /> Próximos Tijolos
              Recomendados Para Você:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {finalReport.recommendedLessonIds.map((lid) => {
                const les = getLessonById(lid);
                if (!les) return null;
                return (
                  <button
                    key={lid}
                    type="button"
                    className="btn btn-ghost"
                    style={{ justifyContent: 'space-between', fontSize: 12.6 }}
                    onClick={() => setModalLesson(les)}
                  >
                    <span style={{ textAlign: 'left' }}>{les.title}</span>
                    <BookOpen size={14} />
                  </button>
                );
              })}
            </div>
          </div>

          <button type="button" className="btn btn-primary btn-block" onClick={resetRun}>
            <RotateCcw size={16} /> Jogar Nova Simulação (Rumo a 8/8 Decisões de Mestre)
          </button>
        </div>
      )}
    </>
  );
};
