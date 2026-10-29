import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, Eye, Pause, Play, Sparkles, Target, X } from 'lucide-react';
import { getExerciseProgressionLadder } from '../engine/exerciseCatalog';
import { AnimationArchetype, ExerciseVariant } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface Props {
  exercise: ExerciseVariant;
  onClose: () => void;
}

interface JointPose {
  head: [number, number];
  shoulder: [number, number];
  elbow: [number, number];
  hand: [number, number];
  hip: [number, number];
  knee: [number, number];
  ankle: [number, number];
  auxLimb?: [number, number, number, number]; // [x1,y1, x2,y2] segunda perna/braco ou equipamento
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpPt(a: [number, number], b: [number, number], t: number): [number, number] {
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
}

function getArchetypePoses(arch: AnimationArchetype): {
  top: JointPose;
  bottom: JointPose;
  propType: 'FLOOR' | 'BENCH' | 'BAR_HIGH' | 'BAR_LOW' | 'WALL';
  activeJoint: 'UPPER' | 'LOWER' | 'CORE';
} {
  switch (arch) {
    case 'PUSH_UP':
      return {
        propType: 'FLOOR',
        activeJoint: 'UPPER',
        top: {
          head: [215, 78],
          shoulder: [192, 92],
          elbow: [188, 124],
          hand: [192, 156],
          hip: [122, 118],
          knee: [78, 136],
          ankle: [38, 154],
        },
        bottom: {
          head: [222, 122],
          shoulder: [194, 134],
          elbow: [166, 120],
          hand: [192, 156],
          hip: [122, 142],
          knee: [78, 149],
          ankle: [38, 154],
        },
      };

    case 'BENCH_PRESS':
      return {
        propType: 'BENCH',
        activeJoint: 'UPPER',
        top: {
          head: [78, 112],
          shoulder: [106, 115],
          elbow: [108, 82],
          hand: [108, 48],
          hip: [164, 118],
          knee: [204, 118],
          ankle: [208, 156],
        },
        bottom: {
          head: [78, 112],
          shoulder: [106, 115],
          elbow: [122, 132],
          hand: [112, 96],
          hip: [164, 118],
          knee: [204, 118],
          ankle: [208, 156],
        },
      };

    case 'OVERHEAD_PRESS':
      return {
        propType: 'FLOOR',
        activeJoint: 'UPPER',
        top: {
          head: [130, 58],
          shoulder: [130, 82],
          elbow: [132, 50],
          hand: [132, 20],
          hip: [130, 122],
          knee: [132, 140],
          ankle: [130, 156],
        },
        bottom: {
          head: [130, 58],
          shoulder: [130, 82],
          elbow: [145, 98],
          hand: [142, 68],
          hip: [130, 122],
          knee: [132, 140],
          ankle: [130, 156],
        },
      };

    case 'ROW_HORIZONTAL':
      return {
        propType: 'BAR_LOW',
        activeJoint: 'UPPER',
        top: {
          head: [184, 72],
          shoulder: [164, 86],
          elbow: [138, 72],
          hand: [158, 102],
          hip: [108, 108],
          knee: [116, 134],
          ankle: [110, 156],
        },
        bottom: {
          head: [184, 74],
          shoulder: [164, 88],
          elbow: [164, 118],
          hand: [166, 144],
          hip: [108, 108],
          knee: [116, 134],
          ankle: [110, 156],
        },
      };

    case 'VERTICAL_PULL':
      return {
        propType: 'BAR_HIGH',
        activeJoint: 'UPPER',
        top: {
          head: [130, 38],
          shoulder: [130, 60],
          elbow: [152, 68],
          hand: [144, 30],
          hip: [130, 104],
          knee: [136, 130],
          ankle: [128, 150],
        },
        bottom: {
          head: [130, 68],
          shoulder: [130, 88],
          elbow: [138, 58],
          hand: [144, 30],
          hip: [130, 128],
          knee: [134, 146],
          ankle: [130, 158],
        },
      };

    case 'SQUAT':
      return {
        propType: 'FLOOR',
        activeJoint: 'LOWER',
        top: {
          head: [132, 42],
          shoulder: [130, 66],
          elbow: [146, 84],
          hand: [152, 68],
          hip: [126, 106],
          knee: [132, 132],
          ankle: [130, 156],
        },
        bottom: {
          head: [140, 74],
          shoulder: [132, 96],
          elbow: [154, 104],
          hand: [162, 88],
          hip: [102, 128],
          knee: [150, 126],
          ankle: [130, 156],
        },
      };

    case 'SPLIT_SQUAT':
      return {
        propType: 'FLOOR',
        activeJoint: 'LOWER',
        top: {
          head: [138, 44],
          shoulder: [136, 68],
          elbow: [138, 92],
          hand: [140, 112],
          hip: [132, 106],
          knee: [154, 130],
          ankle: [152, 156],
          auxLimb: [132, 106, 92, 138],
        },
        bottom: {
          head: [142, 70],
          shoulder: [138, 92],
          elbow: [140, 116],
          hand: [142, 136],
          hip: [130, 128],
          knee: [164, 128],
          ankle: [152, 156],
          auxLimb: [130, 128, 98, 150],
        },
      };

    case 'HIP_HINGE':
      return {
        propType: 'FLOOR',
        activeJoint: 'LOWER',
        top: {
          head: [134, 42],
          shoulder: [132, 66],
          elbow: [134, 92],
          hand: [136, 114],
          hip: [128, 106],
          knee: [132, 132],
          ankle: [130, 156],
        },
        bottom: {
          head: [176, 74],
          shoulder: [156, 86],
          elbow: [152, 112],
          hand: [148, 136],
          hip: [98, 104],
          knee: [122, 132],
          ankle: [130, 156],
        },
      };

    case 'GLUTE_BRIDGE':
      return {
        propType: 'FLOOR',
        activeJoint: 'LOWER',
        top: {
          head: [66, 148],
          shoulder: [92, 148],
          elbow: [116, 152],
          hand: [140, 154],
          hip: [142, 114],
          knee: [184, 96],
          ankle: [192, 156],
        },
        bottom: {
          head: [66, 148],
          shoulder: [92, 148],
          elbow: [116, 152],
          hand: [140, 154],
          hip: [138, 150],
          knee: [180, 108],
          ankle: [192, 156],
        },
      };

    case 'DEADBUG_CORE':
      return {
        propType: 'FLOOR',
        activeJoint: 'CORE',
        top: {
          head: [74, 146],
          shoulder: [98, 148],
          elbow: [100, 118],
          hand: [102, 88],
          hip: [146, 148],
          knee: [148, 112],
          ankle: [182, 112],
        },
        bottom: {
          head: [74, 146],
          shoulder: [98, 148],
          elbow: [72, 138],
          hand: [46, 134],
          hip: [146, 148],
          knee: [182, 140],
          ankle: [218, 142],
        },
      };

    case 'SIDE_PLANK':
      return {
        propType: 'FLOOR',
        activeJoint: 'CORE',
        top: {
          head: [72, 92],
          shoulder: [96, 102],
          elbow: [96, 154],
          hand: [112, 154],
          hip: [148, 124],
          knee: [184, 139],
          ankle: [216, 154],
        },
        bottom: {
          head: [72, 96],
          shoulder: [96, 106],
          elbow: [96, 154],
          hand: [112, 154],
          hip: [148, 129],
          knee: [184, 142],
          ankle: [216, 154],
        },
      };

    case 'MOBILITY_WALL':
      return {
        propType: 'WALL',
        activeJoint: 'UPPER',
        top: {
          head: [118, 46],
          shoulder: [118, 70],
          elbow: [104, 48],
          hand: [96, 26],
          hip: [118, 110],
          knee: [122, 134],
          ankle: [122, 156],
        },
        bottom: {
          head: [118, 46],
          shoulder: [118, 70],
          elbow: [106, 88],
          hand: [96, 66],
          hip: [118, 110],
          knee: [122, 134],
          ankle: [122, 156],
        },
      };

    case 'CARDIO_STRIDE':
    default:
      return {
        propType: 'FLOOR',
        activeJoint: 'LOWER',
        top: {
          head: [138, 42],
          shoulder: [134, 66],
          elbow: [116, 86],
          hand: [132, 98],
          hip: [130, 106],
          knee: [154, 126],
          ankle: [164, 154],
          auxLimb: [130, 106, 104, 150],
        },
        bottom: {
          head: [138, 46],
          shoulder: [134, 70],
          elbow: [148, 86],
          hand: [160, 74],
          hip: [130, 110],
          knee: [114, 132],
          ankle: [98, 154],
          auxLimb: [130, 110, 158, 144],
        },
      };
  }
}

export const ExerciseDemoModal: React.FC<Props> = ({ exercise, onClose }) => {
  const [paused, setPaused] = useState(false);
  const [slowMo, setSlowMo] = useState(false);
  const [phaseTime, setPhaseTime] = useState(0); // 0 .. 5.2s ciclo completo

  useEffect(() => {
    if (paused) return;
    let rafId = 0;
    let last = performance.now();

    const tick = (now: number) => {
      const dt = ((now - last) / 1000) * (slowMo ? 0.45 : 1);
      last = now;
      setPhaseTime((prev) => (prev + dt) % 5.2);
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [paused, slowMo]);

  // Ciclo biomecanico:
  // 0.0 -> 2.4s: Descida / Fase Excentrica Controlada (t: 0 -> 1)
  // 2.4 -> 3.3s: Pausa Estavel de 1s (t = 1)
  // 3.3 -> 4.5s: Subida / Acao Principal (t: 1 -> 0)
  // 4.5 -> 5.2s: Estabilizacao no Topo (t = 0)
  let t = 0;
  let phaseLabel = 'Posição Inicial Firme';
  let phaseColor = '#10b981';

  if (phaseTime < 2.4) {
    const raw = phaseTime / 2.4;
    t = 0.5 - 0.5 * Math.cos(Math.PI * raw);
    phaseLabel = '1. Fase Controlada (Sem Pressa)';
    phaseColor = '#06b6d4';
  } else if (phaseTime < 3.3) {
    t = 1;
    phaseLabel = '2. Pausa Estável (Tensão Ativa)';
    phaseColor = '#f59e0b';
  } else if (phaseTime < 4.5) {
    const raw = (phaseTime - 3.3) / 1.2;
    t = 1 - (0.5 - 0.5 * Math.cos(Math.PI * raw));
    phaseLabel = '3. Ação Principal Firme';
    phaseColor = '#10b981';
  }

  const { top, bottom, propType, activeJoint } = getArchetypePoses(exercise.animationArchetype);

  const pose: JointPose = {
    head: lerpPt(top.head, bottom.head, t),
    shoulder: lerpPt(top.shoulder, bottom.shoulder, t),
    elbow: lerpPt(top.elbow, bottom.elbow, t),
    hand: lerpPt(top.hand, bottom.hand, t),
    hip: lerpPt(top.hip, bottom.hip, t),
    knee: lerpPt(top.knee, bottom.knee, t),
    ankle: lerpPt(top.ankle, bottom.ankle, t),
    auxLimb:
      top.auxLimb && bottom.auxLimb
        ? [
            lerp(top.auxLimb[0], bottom.auxLimb[0], t),
            lerp(top.auxLimb[1], bottom.auxLimb[1], t),
            lerp(top.auxLimb[2], bottom.auxLimb[2], t),
            lerp(top.auxLimb[3], bottom.auxLimb[3], t),
          ]
        : undefined,
  };

  const highlightGlow =
    activeJoint === 'UPPER' ? pose.shoulder : activeJoint === 'LOWER' ? pose.hip : pose.hip;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="section-header" style={{ marginBottom: 8 }}>
          <div>
            <div className="section-kicker">Demonstração Visual &amp; Técnica</div>
            <h2 className="section-title" style={{ fontSize: 17 }}>
              {exercise.name}
            </h2>
          </div>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ minHeight: 36, padding: '6px 10px' }}
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        {/* PALCO CINEMATICO VETORIAL EM TEMPO REAL */}
        <div
          style={{
            position: 'relative',
            borderRadius: 16,
            background: 'radial-gradient(circle at 50% 45%, #162033 0%, #090d16 100%)',
            border: '1px solid rgba(255,255,255,0.1)',
            padding: '10px 12px',
            marginBottom: 14,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 6,
            }}
          >
            <span
              className="badge"
              style={{
                background: 'rgba(15,23,42,0.85)',
                border: `1px solid ${phaseColor}`,
                color: phaseColor,
              }}
            >
              {phaseLabel}
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                className={`chip ${slowMo ? 'chip-active' : ''}`}
                style={{ padding: '4px 9px', fontSize: 11 }}
                onClick={() => {
                  triggerHaptic('light');
                  setSlowMo((s) => !s);
                }}
              >
                {slowMo ? '0.5x Lento' : '1x Real'}
              </button>
              <button
                type="button"
                className="chip"
                style={{ padding: '4px 9px', fontSize: 11 }}
                onClick={() => setPaused((p) => !p)}
              >
                {paused ? <Play size={12} /> : <Pause size={12} />}
              </button>
            </div>
          </div>

          <svg viewBox="0 0 260 172" style={{ width: '100%', height: 'auto', display: 'block' }}>
            {/* Grade sutil de alinhamento postural */}
            <line x1="20" y1="158" x2="240" y2="158" stroke="rgba(255,255,255,0.18)" strokeWidth="2" />
            <line
              x1="130"
              y1="14"
              x2="130"
              y2="158"
              stroke="rgba(255,255,255,0.05)"
              strokeDasharray="3 3"
            />

            {/* Geometria do equipamento/apoio */}
            {propType === 'BENCH' && (
              <g stroke="rgba(148,163,184,0.45)" strokeWidth="4" strokeLinecap="round">
                <line x1="65" y1="125" x2="188" y2="125" />
                <line x1="85" y1="125" x2="85" y2="158" />
                <line x1="172" y1="125" x2="172" y2="158" />
              </g>
            )}
            {propType === 'BAR_HIGH' && (
              <g stroke="#94a3b8" strokeWidth="3.5" strokeLinecap="round">
                <line x1="88" y1="28" x2="172" y2="28" />
                <line x1="94" y1="14" x2="94" y2="158" strokeOpacity="0.25" />
              </g>
            )}
            {propType === 'BAR_LOW' && (
              <g stroke="rgba(148,163,184,0.4)" strokeWidth="3.5" strokeLinecap="round">
                <line x1="168" y1="110" x2="215" y2="110" />
                <line x1="175" y1="110" x2="175" y2="158" />
              </g>
            )}
            {propType === 'WALL' && (
              <line x1="92" y1="16" x2="92" y2="158" stroke="rgba(245,158,11,0.45)" strokeWidth="4" />
            )}

            {/* Halo muscular ativo */}
            <circle cx={highlightGlow[0]} cy={highlightGlow[1]} r="20" fill="rgba(245,158,11,0.16)" />

            {/* Membro auxiliar traseiro (se existir) */}
            {pose.auxLimb && (
              <line
                x1={pose.auxLimb[0]}
                y1={pose.auxLimb[1]}
                x2={pose.auxLimb[2]}
                y2={pose.auxLimb[3]}
                stroke="rgba(148,163,184,0.5)"
                strokeWidth="5"
                strokeLinecap="round"
              />
            )}

            {/* Perna principal (Quadril -> Joelho -> Tornozelo) */}
            <line
              x1={pose.hip[0]}
              y1={pose.hip[1]}
              x2={pose.knee[0]}
              y2={pose.knee[1]}
              stroke="#e2e8f0"
              strokeWidth="6"
              strokeLinecap="round"
            />
            <line
              x1={pose.knee[0]}
              y1={pose.knee[1]}
              x2={pose.ankle[0]}
              y2={pose.ankle[1]}
              stroke="#cbd5e1"
              strokeWidth="5.5"
              strokeLinecap="round"
            />

            {/* Coluna / Tronco alinhado (Quadril -> Ombro) */}
            <line
              x1={pose.hip[0]}
              y1={pose.hip[1]}
              x2={pose.shoulder[0]}
              y2={pose.shoulder[1]}
              stroke="#22d3ee"
              strokeWidth="7"
              strokeLinecap="round"
            />

            {/* Braco principal (Ombro -> Cotovelo -> Mao) */}
            <line
              x1={pose.shoulder[0]}
              y1={pose.shoulder[1]}
              x2={pose.elbow[0]}
              y2={pose.elbow[1]}
              stroke="#f59e0b"
              strokeWidth="5.5"
              strokeLinecap="round"
            />
            <line
              x1={pose.elbow[0]}
              y1={pose.elbow[1]}
              x2={pose.hand[0]}
              y2={pose.hand[1]}
              stroke="#fbbf24"
              strokeWidth="5"
              strokeLinecap="round"
            />

            {/* Cabeca e articulacoes */}
            <circle
              cx={pose.head[0]}
              cy={pose.head[1]}
              r="10"
              fill="#0f172a"
              stroke="#f8fafc"
              strokeWidth="3"
            />
            {[pose.shoulder, pose.elbow, pose.hand, pose.hip, pose.knee, pose.ankle].map((pt, i) => (
              <circle key={i} cx={pt[0]} cy={pt[1]} r="3.6" fill="#f8fafc" />
            ))}
          </svg>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 6,
              marginTop: 6,
              justifyContent: 'center',
            }}
          >
            {exercise.musclesWorked.map((m) => (
              <span key={m} className="badge badge-cyan" style={{ fontSize: 10.5 }}>
                <Target size={10} /> {m}
              </span>
            ))}
          </div>
        </div>

        {/* DICA DE OURO (FOCO EXTERNO DE WULF — META-ANALISE 2021) */}
        <div
          style={{
            padding: '11px 13px',
            borderRadius: 12,
            background: 'var(--amber-soft)',
            border: '1px solid rgba(245,158,11,0.38)',
            marginBottom: 12,
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 800,
              color: 'var(--amber)',
              textTransform: 'uppercase',
              marginBottom: 4,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <Sparkles size={13} /> Dica de Ouro (Foco Externo — Wulf, 2021)
          </div>
          <div style={{ fontSize: 13.8, fontWeight: 600 }}>{exercise.externalFocusCue}</div>
        </div>

        {/* PASSO A PASSO SIMPLES EM 3 ETAPAS */}
        <div style={{ marginBottom: 12 }}>
          <div
            style={{
              fontSize: 12,
              fontWeight: 800,
              color: '#34d399',
              marginBottom: 6,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <CheckCircle2 size={14} /> Como Fazer Passo a Passo ({exercise.tempoCue})
          </div>
          <ol className="reason-list" style={{ marginTop: 4, color: 'var(--text-primary)' }}>
            {exercise.stepByStep.map((s, i) => (
              <li key={i} style={{ marginBottom: 6 }}>
                {s}
              </li>
            ))}
          </ol>
        </div>

        {/* ESCADA BIOMECANICA: DO ZERO AO MESTRE */}
        {(() => {
          const ladder = getExerciseProgressionLadder(exercise);
          return (
            <div
              style={{
                padding: '10px 12px',
                borderRadius: 12,
                background: 'var(--bg-elevated)',
                border: '1px solid rgba(6,182,212,0.34)',
                marginBottom: 12,
                fontSize: 12.6,
              }}
            >
              <div
                style={{
                  fontWeight: 800,
                  color: '#22d3ee',
                  fontSize: 11.2,
                  textTransform: 'uppercase',
                  marginBottom: 6,
                }}
              >
                Escada Biomecânica — Do Zero ao Mestre
              </div>
              <div style={{ marginBottom: 6 }}>
                <strong style={{ color: '#34d399' }}>🟢 Degrau Zero (Se ainda está pesado):</strong>{' '}
                {ladder.zeroStep}
              </div>
              <div>
                <strong style={{ color: '#fbbf24' }}>🟣 Degrau Mestre (Quando ficar fácil):</strong>{' '}
                {ladder.masterStep}
              </div>
            </div>
          );
        })()}

        {/* ERROS COMUNS A EVITAR */}
        <div
          style={{
            padding: '10px 12px',
            borderRadius: 12,
            background: 'var(--crimson-soft)',
            border: '1px solid rgba(239,68,68,0.32)',
            marginBottom: 14,
          }}
        >
          <div
            style={{
              fontSize: 11.5,
              fontWeight: 800,
              color: '#fca5a5',
              marginBottom: 4,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <AlertCircle size={14} /> Evite Estes 2 Erros Comuns
          </div>
          <ul className="reason-list" style={{ marginTop: 2, color: '#fecaca' }}>
            {exercise.commonMistakes.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>

        <button type="button" className="btn btn-primary btn-block" onClick={onClose}>
          <Eye size={16} /> Entendi o Movimento — Voltar ao Treino
        </button>
      </div>
    </div>
  );
};
