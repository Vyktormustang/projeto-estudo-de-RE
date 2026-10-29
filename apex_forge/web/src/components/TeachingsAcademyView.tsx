import React, { useState } from 'react';
import {
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  Compass,
  GraduationCap,
  Layers,
  PlayCircle,
  RefreshCw,
  Search,
  Sparkles,
} from 'lucide-react';
import {
  getDueTeachingsForDay,
  getLessonMasteryTier,
  MASTERY_TIERS,
  TEACHING_TRACKS,
  TEACHINGS_CATALOG,
} from '../engine/teachingsCatalog';
import {
  MasteryTier,
  TeachingLesson,
  TeachingProgressEntry,
  TeachingTrackId,
} from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';
import { TeachingLessonModal } from './TeachingLessonModal';

interface Props {
  bioDayId: string;
  progressMap: Record<string, TeachingProgressEntry>;
  completedFieldMissions?: Record<string, string>;
  onCompleteLessonQuiz: (lesson: TeachingLesson, wasCorrect: boolean) => void;
  onToggleFieldMission?: (lessonId: string) => void;
  onOpenSimulator?: () => void;
}

export const TeachingsAcademyView: React.FC<Props> = ({
  bioDayId,
  progressMap,
  completedFieldMissions = {},
  onCompleteLessonQuiz,
  onToggleFieldMission,
  onOpenSimulator,
}) => {
  const [selectedTier, setSelectedTier] = useState<'TODOS' | MasteryTier>('TODOS');
  const [selectedTrack, setSelectedTrack] = useState<'TODAS' | TeachingTrackId>('TODAS');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeLesson, setActiveLesson] = useState<{
    lesson: TeachingLesson;
    quizFirst: boolean;
  } | null>(null);

  const dueLessons = getDueTeachingsForDay(progressMap, bioDayId);
  const studiedCount = Object.keys(progressMap).length;
  const masteredCount = Object.values(progressMap).filter((p) => p.masteryLevel >= 3).length;
  const missionsDoneCount = Object.keys(completedFieldMissions).length;
  const completionPct = Math.round((studiedCount / TEACHINGS_CATALOG.length) * 100);

  const normalizedQuery = searchQuery.trim().toLowerCase();

  const visibleLessons = TEACHINGS_CATALOG.filter((l) => {
    if (selectedTier !== 'TODOS' && getLessonMasteryTier(l) !== selectedTier) return false;
    if (selectedTrack !== 'TODAS' && l.trackId !== selectedTrack) return false;
    if (!normalizedQuery) return true;
    const hay = `${l.title} ${l.subtitle} ${l.mentorName} ${l.coreEssence}`.toLowerCase();
    return hay.includes(normalizedQuery);
  }).sort((a, b) => getLessonMasteryTier(a) - getLessonMasteryTier(b));

  const activeTrackMeta = TEACHING_TRACKS.find((t) => t.id === selectedTrack);
  const activeTierMeta = MASTERY_TIERS.find((t) => t.tier === selectedTier);

  const handleNextLesson = () => {
    if (!activeLesson) return;
    const list = visibleLessons.length > 0 ? visibleLessons : TEACHINGS_CATALOG;
    const curIdx = list.findIndex((x) => x.id === activeLesson.lesson.id);
    const nextItem = list[(curIdx + 1) % list.length];
    setActiveLesson({ lesson: nextItem, quizFirst: false });
  };

  return (
    <>
      {activeLesson && (
        <TeachingLessonModal
          key={activeLesson.lesson.id}
          lesson={activeLesson.lesson}
          existingProgress={progressMap[activeLesson.lesson.id]}
          fieldMissionDone={Boolean(completedFieldMissions[activeLesson.lesson.id])}
          startInQuizMode={activeLesson.quizFirst}
          onCompleteQuiz={onCompleteLessonQuiz}
          onToggleFieldMission={onToggleFieldMission}
          onNextLesson={visibleLessons.length > 1 ? handleNextLesson : undefined}
          onClose={() => setActiveLesson(null)}
        />
      )}

      {/* PAINEL DA BASE ABSOLUTA: 10 PILARES x 4 GRAUS = 60 LICOES */}
      <div className="card card-amber">
        <div className="section-header">
          <div>
            <div className="section-kicker">
              A Base Absoluta • 10 Pilares Universais • {TEACHINGS_CATALOG.length} Lições
            </div>
            <h2 className="section-title">A Pedra Angular &amp; Árvore do Mestre Universal</h2>
          </div>
          <GraduationCap size={23} color="var(--amber)" />
        </div>

        <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
          Coroada pelos ensinamentos do maior Mestre que já pisou na Terra —{' '}
          <strong>Jesus Cristo</strong> — e pela <strong>Sabedoria da Bíblia</strong>, a Base
          Absoluta reúne <strong>10 Pilares Fundacionais × 20 Lições = 200 Lições Canônicas</strong>{' '}
          em simetria cristalina nos <strong>4 Graus Progressivos (50 por Grau)</strong>!
        </p>

        <div className="grid-3" style={{ marginBottom: 12 }}>
          <div className="metric-box">
            <div className="metric-label">Base Estudada</div>
            <div className="metric-value">
              {studiedCount}/{TEACHINGS_CATALOG.length}
            </div>
            <div className="metric-sub">{completionPct}% concluído</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Missões Reais</div>
            <div className="metric-value" style={{ color: '#34d399' }}>
              {missionsDoneCount}
            </div>
            <div className="metric-sub">Na vida real</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Revisão Hoje</div>
            <div
              className="metric-value"
              style={{ color: dueLessons.length > 0 ? '#fbbf24' : '#34d399' }}
            >
              {dueLessons.length}
            </div>
            <div className="metric-sub">{masteredCount} dominadas</div>
          </div>
        </div>

        <div className="progress-track" style={{ marginBottom: 12 }}>
          <div className="progress-fill" style={{ width: `${completionPct}%` }} />
        </div>

        {/* PROGRESSO POR GRAU (ARVORE DE ANDAIMES 4C/ID) */}
        <div className="grid-2" style={{ gap: 8, marginBottom: onOpenSimulator ? 12 : 0 }}>
          {MASTERY_TIERS.map((tm) => {
            const tierLessons = TEACHINGS_CATALOG.filter((l) => getLessonMasteryTier(l) === tm.tier);
            const tierDone = tierLessons.filter((l) => Boolean(progressMap[l.id])).length;
            const isSelected = selectedTier === tm.tier;
            return (
              <button
                key={tm.tier}
                type="button"
                onClick={() => {
                  triggerHaptic('light');
                  setSelectedTier(isSelected ? 'TODOS' : tm.tier);
                }}
                style={{
                  textAlign: 'left',
                  padding: '9px 10px',
                  borderRadius: 12,
                  background: isSelected ? 'var(--amber-soft)' : 'var(--bg-elevated)',
                  border: isSelected
                    ? '1.5px solid var(--amber)'
                    : '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: 11.5,
                    fontWeight: 800,
                    color: isSelected ? '#fbbf24' : 'var(--text-primary)',
                  }}
                >
                  <span>{tm.badgeLabel}</span>
                  <span className="mono" style={{ color: '#34d399' }}>
                    {tierDone}/{tierLessons.length}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {onOpenSimulator && (
          <button
            type="button"
            className="btn btn-emerald btn-block"
            onClick={() => {
              triggerHaptic('medium');
              onOpenSimulator();
            }}
          >
            <Compass size={16} /> Jogar Simulador Vivo: &ldquo;Jovem do Zero ao Mestre&rdquo;
          </button>
        )}

        {dueLessons.length > 0 && (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 12,
              background: 'var(--cyan-soft)',
              border: '1px solid rgba(6,182,212,0.4)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 10,
              flexWrap: 'wrap',
            }}
          >
            <div style={{ fontSize: 13 }}>
              <strong style={{ color: '#22d3ee' }}>
                <RefreshCw size={13} style={{ verticalAlign: 'middle' }} /> Revisão Espaçada Ideal:
              </strong>{' '}
              {dueLessons[0].title}
            </div>
            <button
              type="button"
              className="btn btn-primary"
              style={{ minHeight: 36, padding: '6px 12px', fontSize: 12.5 }}
              onClick={() => {
                triggerHaptic('light');
                setActiveLesson({ lesson: dueLessons[0], quizFirst: true });
              }}
            >
              Revisar em 30s
            </button>
          </div>
        )}
      </div>

      {/* BUSCA RAPIDA + FILTRO DE GRAU + 10 PILARES */}
      <div className="card" style={{ padding: 14 }}>
        <div style={{ position: 'relative', marginBottom: 12 }}>
          <Search
            size={15}
            color="var(--text-muted)"
            style={{ position: 'absolute', left: 12, top: 13 }}
          />
          <input
            className="input"
            style={{ paddingLeft: 36 }}
            placeholder="Buscar tema, mentor ou dificuldade (ex: Cristo, perdão, foco, sono, dinheiro)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="section-kicker" style={{ marginBottom: 6 }}>
          <Layers size={12} style={{ verticalAlign: 'middle' }} /> Filtrar pelos 10 Pilares da Base
          Absoluta
        </div>
        <div className="chip-row">
          <button
            type="button"
            className={`chip ${selectedTrack === 'TODAS' ? 'chip-active' : ''}`}
            onClick={() => {
              triggerHaptic('light');
              setSelectedTrack('TODAS');
            }}
          >
            Todos os 10 ({TEACHINGS_CATALOG.length})
          </button>
          {TEACHING_TRACKS.map((tr) => (
            <button
              key={tr.id}
              type="button"
              className={`chip ${selectedTrack === tr.id ? 'chip-active' : ''}`}
              onClick={() => {
                triggerHaptic('light');
                setSelectedTrack(tr.id);
              }}
            >
              {tr.shortLabel}
            </button>
          ))}
        </div>

        {activeTierMeta && (
          <div className="muted" style={{ marginTop: 10, fontSize: 12.6, color: '#fde68a' }}>
            <strong>{activeTierMeta.title}:</strong> {activeTierMeta.subtitle}{' '}
            <button
              type="button"
              className="chip"
              style={{ padding: '2px 8px', fontSize: 11, marginLeft: 4 }}
              onClick={() => setSelectedTier('TODOS')}
            >
              Ver todos os graus
            </button>
          </div>
        )}

        {activeTrackMeta && (
          <div className="muted" style={{ marginTop: 8, fontSize: 12.6 }}>
            <strong>{activeTrackMeta.title}:</strong> {activeTrackMeta.description}
          </div>
        )}
      </div>

      {/* LISTA DE ENSINAMENTOS INTERATIVOS ORDENADOS DO GRAU I AO IV */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
        {visibleLessons.map((lesson) => {
          const prog = progressMap[lesson.id];
          const tier = getLessonMasteryTier(lesson);
          const tierBadge = MASTERY_TIERS.find((t) => t.tier === tier)?.badgeLabel ?? `Grau ${tier}`;
          const missionDone = Boolean(completedFieldMissions[lesson.id]);
          const isDue =
            prog && prog.lastStudiedBioDayId < bioDayId && prog.nextReviewBioDayId <= bioDayId;

          return (
            <div className="card" key={lesson.id} style={{ padding: 15 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: 10,
                }}
              >
                <div>
                  <div className="section-kicker" style={{ marginBottom: 3 }}>
                    {tierBadge} • {lesson.mentorName}
                  </div>
                  <h3 className="section-title" style={{ fontSize: 15.8 }}>
                    {lesson.title}
                  </h3>
                  <div className="muted" style={{ fontSize: 12.5, marginTop: 3 }}>
                    {lesson.subtitle}
                  </div>
                </div>

                {prog ? (
                  <span
                    className={`badge ${
                      isDue
                        ? 'badge-yellow'
                        : prog.masteryLevel >= 3
                          ? 'badge-green'
                          : 'badge-cyan'
                    }`}
                    style={{ flexShrink: 0 }}
                  >
                    {isDue ? (
                      'Revisar Hoje'
                    ) : prog.masteryLevel >= 4 ? (
                      <>
                        <Award size={11} /> Dominado
                      </>
                    ) : (
                      <>
                        <CheckCircle2 size={11} /> Nv {prog.masteryLevel}/4
                      </>
                    )}
                  </span>
                ) : (
                  <span className="badge badge-yellow" style={{ flexShrink: 0 }}>
                    <Sparkles size={10} /> Novo
                  </span>
                )}
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: 12,
                  gap: 8,
                  flexWrap: 'wrap',
                }}
              >
                <span className="muted" style={{ fontSize: 11.8 }}>
                  <Clock size={12} style={{ verticalAlign: 'middle' }} /> ~{lesson.readTimeSec}s
                  {missionDone && (
                    <span style={{ color: '#34d399', fontWeight: 700, marginLeft: 8 }}>
                      • ✓ Aplicado na Vida Real
                    </span>
                  )}
                </span>

                <div style={{ display: 'flex', gap: 6 }}>
                  {isDue && (
                    <button
                      type="button"
                      className="btn btn-emerald"
                      style={{ minHeight: 36, padding: '6px 12px', fontSize: 12.5 }}
                      onClick={() => {
                        triggerHaptic('light');
                        setActiveLesson({ lesson, quizFirst: true });
                      }}
                    >
                      Teste Rápido
                    </button>
                  )}
                  <button
                    type="button"
                    className={`btn ${prog ? 'btn-ghost' : 'btn-primary'}`}
                    style={{ minHeight: 36, padding: '6px 13px', fontSize: 12.5 }}
                    onClick={() => {
                      triggerHaptic('light');
                      setActiveLesson({ lesson, quizFirst: false });
                    }}
                  >
                    {prog ? (
                      <>
                        <BookOpen size={14} /> Rever
                      </>
                    ) : (
                      <>
                        <PlayCircle size={14} /> Estudar Lição
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};
