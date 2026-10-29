import React, { useEffect, useState } from 'react';
import {
  Brain,
  CheckCircle2,
  Eye,
  GraduationCap,
  Play,
  Sparkles,
  Square,
  Timer,
  Volume2,
  VolumeX,
  Wind,
  Zap,
} from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import {
  CognitiveChallengeLog,
  DeliberatePracticeLog,
  IfThenContract,
  SkillBlueprint,
  TeachingLesson,
  TeachingProgressEntry,
  UserProfile,
} from '../engine/types';
import { playBreathPhaseCue, playTacticalChime } from '../services/audioBiofeedback';
import { setWakeLock, triggerHaptic } from '../services/vaultStorage';
import { CognitiveArena } from './CognitiveArena';
import { SkillForgeBuilderView } from './SkillForgeBuilderView';
import { TeachingsAcademyView } from './TeachingsAcademyView';
import { PomodoroTimer } from './PomodoroTimer';

interface Props {
  bioDayId: string;
  profile: UserProfile;
  mentalSessionsCount: number;
  practiceLogs: DeliberatePracticeLog[];
  cognitiveLogs: CognitiveChallengeLog[];
  skillBlueprints?: SkillBlueprint[];
  teachingProgress: Record<string, TeachingProgressEntry>;
  completedFieldMissions?: Record<string, string>;
  onRecordMentalSession: () => void;
  onSaveDeliberateLog: (log: DeliberatePracticeLog) => void;
  onSaveCognitiveLog: (log: CognitiveChallengeLog) => void;
  onSaveBlueprints?: (next: SkillBlueprint[]) => void;
  onAddIfThen?: (contract: IfThenContract) => void;
  onCompleteLessonQuiz: (lesson: TeachingLesson, wasCorrect: boolean) => void;
  onToggleFieldMission: (lessonId: string) => void;
}

type CortexSection = 'DESAFIOS' | 'LICOES' | 'RESPIRACAO' | 'ESTUDO';

export const CortexTab: React.FC<Props> = ({
  bioDayId,
  profile,
  mentalSessionsCount,
  practiceLogs,
  cognitiveLogs,
  skillBlueprints = [],
  teachingProgress,
  completedFieldMissions = {},
  onRecordMentalSession,
  onSaveDeliberateLog,
  onSaveCognitiveLog,
  onSaveBlueprints,
  onAddIfThen,
  onCompleteLessonQuiz,
  onToggleFieldMission,
}) => {
  const [section, setSection] = useState<CortexSection>('DESAFIOS');

  // Laboratorio Autonomico 3-Protocolos (Suspiro Stanford 2023 / Coerencia 0.1 Hz / Box 4-4-4-4)
  const [breathProtocol, setBreathProtocol] = useState<
    'SUSPIRO_STANFORD' | 'COERENCIA_01HZ' | 'BOX_TATICO'
  >('SUSPIRO_STANFORD');
  const [breathingActive, setBreathingActive] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [breathElapsedSec, setBreathElapsedSec] = useState(0);
  const [eyesOpenMode, setEyesOpenMode] = useState(profile.clinical.interoceptiveSensitive);
  const [sessionLoggedOnce, setSessionLoggedOnce] = useState(false);

  // Pratica Deliberada + Cronometro Ao Vivo Ultradiano (Ericsson; Kleitman; Dunstan 2012)
  const [subSkill, setSubSkill] = useState(profile.primaryGoalDomain);
  const [durationMinutes, setDurationMinutes] = useState('50');
  const [keyCorrectionNote, setKeyCorrectionNote] = useState('');
  const [feynmanPass, setFeynmanPass] = useState(true);
  const [attemptsCount, setAttemptsCount] = useState('6');
  const [errorsCount, setErrorsCount] = useState('2');
  const [focusTargetMin, setFocusTargetMin] = useState<25 | 50 | 90>(50);
  const [focusRunning, setFocusRunning] = useState(false);
  const [focusRemainingSec, setFocusRemainingSec] = useState(50 * 60);
  const [focusBreakAlert, setFocusBreakAlert] = useState(false);

  useEffect(() => {
    setWakeLock(breathingActive || focusRunning);
    return () => {
      setWakeLock(false);
    };
  }, [breathingActive, focusRunning]);

  useEffect(() => {
    if (!focusRunning) return;
    const id = window.setInterval(() => {
      setFocusRemainingSec((prev) => {
        if (prev <= 1) {
          setFocusRunning(false);
          setFocusBreakAlert(true);
          setDurationMinutes(String(focusTargetMin));
          triggerHaptic('success');
          playTacticalChime('REST_DONE');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [focusRunning, focusTargetMin]);

  useEffect(() => {
    if (!breathingActive) return;
    const id = window.setInterval(() => {
      setBreathElapsedSec((prev) => {
        const next = prev + 1;
        if (breathProtocol === 'SUSPIRO_STANFORD') {
          const pos = next % 10;
          if (pos === 0) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('INHALE');
          } else if (pos === 3) {
            triggerHaptic('medium');
            if (soundEnabled) playBreathPhaseCue('TOP_SIGH');
          } else if (pos === 4) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('EXHALE');
          }
        } else if (breathProtocol === 'COERENCIA_01HZ') {
          const pos = next % 10;
          if (pos === 0) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('INHALE');
          } else if (pos === 4) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('EXHALE');
          }
        } else {
          const pos = next % 16;
          if (pos === 0) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('INHALE');
          } else if (pos === 4 || pos === 12) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('HOLD');
          } else if (pos === 8) {
            triggerHaptic('light');
            if (soundEnabled) playBreathPhaseCue('EXHALE');
          }
        }

        if (next === 60 && !sessionLoggedOnce) {
          setSessionLoggedOnce(true);
          onRecordMentalSession();
        }
        return next;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [breathingActive, breathProtocol, soundEnabled, sessionLoggedOnce, onRecordMentalSession]);

  const computeBreathDisplay = (): { label: string; scale: number } => {
    if (!breathingActive) return { label: 'TOQUE INICIAR', scale: 1.0 };
    if (breathProtocol === 'SUSPIRO_STANFORD') {
      const pos = breathElapsedSec % 10;
      if (pos < 3) return { label: `PUXE PELO NARIZ (${3 - pos}s)`, scale: 1.14 };
      if (pos < 4) return { label: '2ª PUXADINHA NO TOPO! (1s)', scale: 1.24 };
      return { label: `SOLTE LENTO PELA BOCA (${10 - pos}s)`, scale: 0.85 };
    }
    if (breathProtocol === 'COERENCIA_01HZ') {
      const pos = breathElapsedSec % 10;
      if (pos < 4) return { label: `PUXE O AR (${4 - pos}s)`, scale: 1.18 };
      return { label: `SOLTE DEVAGAR (${10 - pos}s)`, scale: 0.86 };
    }
    const pos = breathElapsedSec % 16;
    if (pos < 4) return { label: `INSPIRE (${4 - pos}s)`, scale: 1.18 };
    if (pos < 8) return { label: `SEGURE SUAVE (${8 - pos}s)`, scale: 1.18 };
    if (pos < 12) return { label: `SOLTE (${12 - pos}s)`, scale: 0.86 };
    return { label: `PAUSA VAZIA (${16 - pos}s)`, scale: 0.86 };
  };

  const breathDisplay = computeBreathDisplay();
  const orbScale = breathDisplay.scale;

  const handleSavePractice = () => {
    if (!keyCorrectionNote.trim()) return;
    triggerHaptic('success');
    playTacticalChime('VICTORY');
    onSaveDeliberateLog({
      id: `dp_${Date.now()}`,
      bioDayId,
      timestampMs: Date.now(),
      subSkill: subSkill.trim() || profile.primaryGoalDomain,
      objectiveOracleCriteria: 'Feedback real medido em tentativas e erros corrigidos',
      durationMinutes: Math.max(5, Math.min(300, Math.round(Number(durationMinutes) || 30))),
      attemptsCount: Math.max(1, Math.round(Number(attemptsCount) || 1)),
      errorsCount: Math.max(0, Math.round(Number(errorsCount) || 0)),
      feynmanPass,
      keyCorrectionNote: keyCorrectionNote.trim(),
      nextReviewBioDayId: addDaysToBioDay(bioDayId, 3),
    });
    setKeyCorrectionNote('');
  };

  return (
    <>
      {/* SELETOR LIMPO DE 4 AREAS MENTAIS */}
      <div
        className="card"
        style={{
          padding: 8,
          display: 'grid',
          gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
          gap: 6,
        }}
      >
        <button
          type="button"
          className={`btn ${section === 'DESAFIOS' ? 'btn-primary' : 'btn-ghost'}`}
          style={{ minHeight: 42, padding: '8px 4px', fontSize: 12 }}
          onClick={() => {
            triggerHaptic('light');
            setSection('DESAFIOS');
          }}
        >
          <Zap size={14} /> Desafios
        </button>
        <button
          type="button"
          className={`btn ${section === 'LICOES' ? 'btn-primary' : 'btn-ghost'}`}
          style={{ minHeight: 42, padding: '8px 4px', fontSize: 12 }}
          onClick={() => {
            triggerHaptic('light');
            setSection('LICOES');
          }}
        >
          <GraduationCap size={14} /> Lições
        </button>
        <button
          type="button"
          className={`btn ${section === 'RESPIRACAO' ? 'btn-primary' : 'btn-ghost'}`}
          style={{ minHeight: 42, padding: '8px 4px', fontSize: 12 }}
          onClick={() => {
            triggerHaptic('light');
            setSection('RESPIRACAO');
          }}
        >
          <Wind size={14} /> Calma
        </button>
        <button
          type="button"
          className={`btn ${section === 'ESTUDO' ? 'btn-primary' : 'btn-ghost'}`}
          style={{ minHeight: 42, padding: '8px 4px', fontSize: 12 }}
          onClick={() => {
            triggerHaptic('light');
            setSection('ESTUDO');
          }}
        >
          <Brain size={14} /> Estudo
        </button>
      </div>

      {/* 1. ARENA INTERATIVA DE DESAFIOS MENTAIS */}
      {section === 'DESAFIOS' && (
        <CognitiveArena
          bioDayId={bioDayId}
          logs={cognitiveLogs}
          onSaveLog={onSaveCognitiveLog}
        />
      )}

      {/* 2. ACADEMIA DE ENSINAMENTOS APLICADOS */}
      {section === 'LICOES' && (
        <TeachingsAcademyView
          bioDayId={bioDayId}
          progressMap={teachingProgress}
          completedFieldMissions={completedFieldMissions}
          onCompleteLessonQuiz={onCompleteLessonQuiz}
          onToggleFieldMission={onToggleFieldMission}
        />
      )}

      {/* 2. RESPIRACAO GUIADA 0.1 Hz */}
      {section === 'RESPIRACAO' && (
        <div className="card card-cyan">
          <div className="section-header">
            <div>
              <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
                Laboratório Autonômico Ao Vivo • {mentalSessionsCount} sessões concluídas
              </div>
              <h2 className="section-title">Regulação Vagal &amp; Controle Sob Pressão</h2>
            </div>
            <button type="button" className="chip" onClick={() => setSoundEnabled((s) => !s)}>
              {soundEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}{' '}
              {soundEnabled ? 'Som Ligado' : 'Mudo'}
            </button>
          </div>

          <div className="chip-row" style={{ marginBottom: 10 }}>
            {[
              {
                id: 'SUSPIRO_STANFORD' as const,
                label: 'Suspiro Fisiológico (Stanford)',
              },
              {
                id: 'COERENCIA_01HZ' as const,
                label: 'Coerência 0,1 Hz (4-6s)',
              },
              {
                id: 'BOX_TATICO' as const,
                label: 'Caixa Tática (4-4-4-4)',
              },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                className={`chip ${breathProtocol === p.id ? 'chip-active' : ''}`}
                onClick={() => {
                  triggerHaptic('light');
                  setBreathProtocol(p.id);
                  setBreathElapsedSec(0);
                }}
              >
                {p.label}
              </button>
            ))}
          </div>

          <p className="muted" style={{ marginTop: 0 }}>
            {breathProtocol === 'SUSPIRO_STANFORD' ? (
              <>
                <strong>RCT Cell Reports Medicine (Balban &amp; Huberman, 2023):</strong> puxe pelo
                nariz (<strong>3s</strong>) + dê uma 2ª puxadinha curta no topo (<strong>1s</strong>
                ) + solte devagar pela boca (<strong>6s</strong>). Superou meditação passiva na
                melhora do humor e redução da frequência respiratória!
              </>
            ) : breathProtocol === 'COERENCIA_01HZ' ? (
              <>
                <strong>Coerência Cardiorrespiratória (Lehrer &amp; Gevirtz):</strong> puxe
                suavemente por <strong>4s</strong> e solte por <strong>6s</strong> (6 ciclos/min)
                para acalmar antes de estudar ou dormir.
              </>
            ) : (
              <>
                <strong>Respiração em Caixa 4-4-4-4:</strong> estabiliza o ritmo antes de provas,
                entrevistas ou negociações tensas (mantenha as pausas suaves, sem forçar pressão).
              </>
            )}
          </p>

          <div className="chip-row" style={{ marginBottom: 8 }}>
            <button
              type="button"
              className={`chip ${!eyesOpenMode ? 'chip-active' : ''}`}
              disabled={profile.clinical.interoceptiveSensitive}
              onClick={() => setEyesOpenMode(false)}
            >
              Olhos Relaxados
            </button>
            <button
              type="button"
              className={`chip ${eyesOpenMode ? 'chip-active' : ''}`}
              onClick={() => setEyesOpenMode(true)}
            >
              <Eye size={12} /> Olhos Abertos &amp; Pés no Chão
            </button>
          </div>

          {eyesOpenMode && (
            <div
              style={{
                padding: '9px 12px',
                borderRadius: 10,
                background: 'var(--bg-elevated)',
                fontSize: 12.5,
                color: '#67e8f9',
                marginBottom: 8,
              }}
            >
              Mantenha os olhos abertos olhando suavemente para o círculo e sinta os pés apoiados no
              chão. Se sentir qualquer desconforto, pare quando quiser.
            </div>
          )}

          <div className="breath-orb-wrap">
            <div className="breath-orb" style={{ transform: `scale(${orbScale})` }}>
              <div style={{ fontSize: 14.5, fontWeight: 800, color: '#67e8f9', padding: '0 8px' }}>
                {breathDisplay.label}
              </div>
              <div className="mono muted" style={{ marginTop: 4 }}>
                {Math.floor(breathElapsedSec / 60)}:
                {String(breathElapsedSec % 60).padStart(2, '0')}
              </div>
            </div>
          </div>

          {sessionLoggedOnce && (
            <div
              style={{
                marginBottom: 10,
                fontSize: 12.5,
                color: '#34d399',
                textAlign: 'center',
                fontWeight: 700,
              }}
            >
              <CheckCircle2 size={14} style={{ verticalAlign: 'middle' }} /> Sessão registrada no
              seu histórico!
            </div>
          )}

          <div className="grid-2">
            <button
              className={`btn ${breathingActive ? 'btn-danger' : 'btn-primary'}`}
              onClick={() => {
                triggerHaptic('medium');
                if (!breathingActive && soundEnabled) playBreathPhaseCue('INHALE');
                setBreathingActive((a) => !a);
              }}
            >
              {breathingActive ? (
                <>
                  <Square size={15} /> Pausar
                </>
              ) : (
                <>
                  <Play size={15} /> Iniciar Respiração
                </>
              )}
            </button>
            <button
              className="btn btn-ghost"
              onClick={() => {
                setBreathingActive(false);
                setBreathElapsedSec(0);
                setSessionLoggedOnce(false);
              }}
            >
              Zerar Tempo
            </button>
          </div>
        </div>
      )}

      {/* 3. CONSTRUTOR 4C/ID + CRONOMETRO ULTRADIANO AO VIVO + DIARIO DE ESTUDO */}
      {section === 'ESTUDO' && (
        <>
          <div className="card card-cyan">
            <div className="section-header">
              <div>
                <div className="section-kicker">
                  Ciclo Ultradiano (Kleitman) • Pausa Ativa (Dunstan, 2012) • Ericsson
                </div>
                <h2 className="section-title">Cronômetro de Trabalho Profundo</h2>
              </div>
              <Timer size={21} color="var(--cyan)" />
            </div>

            <p className="muted" style={{ marginTop: 0, marginBottom: 10 }}>
              Deixe o celular em modo silencioso fora do alcance visual ou com este painel travado
              sem notificações. Ao encerrar, levante-se por <strong>2 minutos</strong> sem tela.
            </p>

            <div className="chip-row" style={{ marginBottom: 10 }}>
              {([25, 50, 90] as const).map((min) => (
                <button
                  key={min}
                  type="button"
                  className={`chip ${focusTargetMin === min ? 'chip-active' : ''}`}
                  onClick={() => {
                    setFocusRunning(false);
                    setFocusBreakAlert(false);
                    setFocusTargetMin(min);
                    setFocusRemainingSec(min * 60);
                    setDurationMinutes(String(min));
                  }}
                >
                  {min === 25
                    ? '25 min • Sprint Inicial'
                    : min === 50
                      ? '50 min • Bloco Profundo'
                      : '90 min • Teto Ultradiano'}
                </button>
              ))}
            </div>

            <div
              style={{
                padding: '14px 12px',
                borderRadius: 14,
                background: 'var(--bg-elevated)',
                textAlign: 'center',
                marginBottom: 10,
              }}
            >
              <div className="mono" style={{ fontSize: 34, fontWeight: 900, color: '#67e8f9' }}>
                {String(Math.floor(focusRemainingSec / 60)).padStart(2, '0')}:
                {String(focusRemainingSec % 60).padStart(2, '0')}
              </div>
              <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                {focusRunning
                  ? 'Tela protegida por WakeLock • Foco em 1 única tarefa sem alternar abas'
                  : 'Escolha o bloco e registre cada tentativa e erro corrigido em tempo real'}
              </div>

              <div className="grid-2" style={{ marginTop: 10 }}>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    triggerHaptic('light');
                    setAttemptsCount((prev) => String((parseInt(prev, 10) || 0) + 1));
                  }}
                >
                  +1 Tentativa ({attemptsCount})
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    triggerHaptic('medium');
                    setAttemptsCount((prev) => String((parseInt(prev, 10) || 0) + 1));
                    setErrorsCount((prev) => String((parseInt(prev, 10) || 0) + 1));
                  }}
                >
                  +1 Erro Corrigido ({errorsCount})
                </button>
              </div>
            </div>

            {focusBreakAlert && (
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: 12,
                  background: 'var(--emerald-soft)',
                  border: '1px solid rgba(16,185,129,0.4)',
                  fontSize: 12.5,
                  marginBottom: 10,
                }}
              >
                <strong>Bloco concluído!</strong> Levante-se agora por 2 a 3 minutos (água, passos
                leves, olhar horizonte a 6m — Dunstan et al., 2012) e depois salve seu resumo de
                Feynman abaixo.
              </div>
            )}

            <div className="grid-2">
              <button
                type="button"
                className={`btn ${focusRunning ? 'btn-danger' : 'btn-primary'}`}
                onClick={() => {
                  triggerHaptic('medium');
                  setFocusBreakAlert(false);
                  setFocusRunning((r) => !r);
                }}
              >
                {focusRunning ? (
                  <>
                    <Square size={15} /> Pausar Bloco
                  </>
                ) : (
                  <>
                    <Play size={15} /> Iniciar Foco Real
                  </>
                )}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  const elapsedMin = Math.max(
                    5,
                    Math.round((focusTargetMin * 60 - focusRemainingSec) / 60) || focusTargetMin,
                  );
                  setFocusRunning(false);
                  setDurationMinutes(String(elapsedMin));
                  setFocusRemainingSec(focusTargetMin * 60);
                  triggerHaptic('light');
                }}
              >
                Usar Minutos no Diário ({durationMinutes}m)
              </button>
            </div>
          </div>

          <SkillForgeBuilderView
            bioDayId={bioDayId}
            blueprints={skillBlueprints}
            onSaveBlueprints={(next) => onSaveBlueprints?.(next)}
            onSaveDeliberateLog={onSaveDeliberateLog}
            onAddIfThen={onAddIfThen}
          />

          <div className="card card-amber">
            <div className="section-kicker">Registro Rápido de Bloco Prático</div>
            <h2 className="section-title">Diário de Estudo &amp; Prática Focada</h2>
            <p className="muted" style={{ marginTop: 4 }}>
              Para ficar excelente em uma habilidade real (programação, medicina, idiomas, música,
              xadrez), pratique corrigindo seus erros e resuma o que aprendeu com palavras simples.
            </p>

          <div className="grid-2">
            <div className="field">
              <label>Habilidade ou tema estudado</label>
              <input
                className="input"
                value={subSkill}
                onChange={(e) => setSubSkill(e.target.value)}
              />
            </div>
            <div className="field">
              <label>Minutos de foco real</label>
              <input
                type="number"
                className="input"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="field">
              <label>Exercícios / tentativas feitas</label>
              <input
                type="number"
                className="input"
                value={attemptsCount}
                onChange={(e) => setAttemptsCount(e.target.value)}
              />
            </div>
            <div className="field">
              <label>Erros identificados e corrigidos</label>
              <input
                type="number"
                className="input"
                value={errorsCount}
                onChange={(e) => setErrorsCount(e.target.value)}
              />
            </div>
          </div>

          <div className="field">
            <label>Explique em frases simples o que você aprendeu ou corrigiu hoje</label>
            <textarea
              className="textarea"
              placeholder="Ex.: Descobri onde eu errava na lógica X e como resolver..."
              value={keyCorrectionNote}
              onChange={(e) => setKeyCorrectionNote(e.target.value)}
            />
          </div>

          <label className="check-toggle">
            <input
              type="checkbox"
              checked={feynmanPass}
              onChange={(e) => setFeynmanPass(e.target.checked)}
            />
            <div>
              <strong>Teste Feynman aprovado</strong>
              <div className="muted">
                Consigo explicar esse conceito de forma clara sem enrolar em termos difíceis.
              </div>
            </div>
          </label>

          <button className="btn btn-primary btn-block" onClick={handleSavePractice}>
            <Sparkles size={16} /> Salvar Sessão de Estudo
          </button>

          {practiceLogs.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div className="section-kicker" style={{ marginBottom: 6 }}>
                Últimos Estudos Salvos ({practiceLogs.length})
              </div>
              {practiceLogs
                .slice(-3)
                .reverse()
                .map((p) => (
                  <div
                    key={p.id}
                    style={{
                      padding: 10,
                      borderRadius: 10,
                      background: 'var(--bg-elevated)',
                      marginBottom: 6,
                      fontSize: 12.8,
                    }}
                  >
                    <strong>
                      {p.subSkill} ({p.durationMinutes} min • {p.errorsCount} erros corrigidos)
                    </strong>
                    <div className="muted" style={{ marginTop: 3 }}>
                      {p.keyCorrectionNote}
                    </div>
                  </div>
                ))}
            </div>
          )}
          </div>
          <PomodoroTimer bioDayId={bioDayId} />
        </>
      )}
    </>
  );
};
