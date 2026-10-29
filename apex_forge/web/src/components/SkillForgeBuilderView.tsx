import React, { useState } from 'react';
import {
  Award,
  CheckCircle2,
  Compass,
  Layers,
  Plus,
  Shield,
  Sparkles,
  Trash2,
} from 'lucide-react';
import {
  createBlueprintFromTemplate,
  createCustomSkillBlueprint,
  evaluateFeynmanSocraticAudit,
  FeynmanAuditResult,
  PRESET_SKILL_TEMPLATES,
} from '../engine/skillForgeEngine';
import { addDaysToBioDay } from '../engine/stateEngine';
import {
  DeliberatePracticeLog,
  IfThenContract,
  SkillBlueprint,
} from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { triggerHaptic } from '../services/vaultStorage';

interface Props {
  bioDayId: string;
  blueprints: SkillBlueprint[];
  onSaveBlueprints: (next: SkillBlueprint[]) => void;
  onSaveDeliberateLog: (log: DeliberatePracticeLog) => void;
  onAddIfThen?: (contract: IfThenContract) => void;
}

export const SkillForgeBuilderView: React.FC<Props> = ({
  bioDayId,
  blueprints,
  onSaveBlueprints,
  onSaveDeliberateLog,
  onAddIfThen,
}) => {
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customName, setCustomName] = useState('');
  const [customOracle, setCustomOracle] = useState('');
  const [customZero, setCustomZero] = useState('');
  const [customAnalogy, setCustomAnalogy] = useState('');
  const [customSaboteur, setCustomSaboteur] = useState('');

  // Exame Socratico de Feynman (Chi + Feynman)
  const [selectedBpId, setSelectedBpId] = useState<string>('LIVRE');
  const [conceptName, setConceptName] = useState('');
  const [childExp, setChildExp] = useState('');
  const [whyBoundary, setWhyBoundary] = useState('');
  const [analogyText, setAnalogyText] = useState('');
  const [auditResult, setAuditResult] = useState<FeynmanAuditResult | null>(null);
  const [shieldCreatedId, setShieldCreatedId] = useState<string | null>(null);

  const handleAddPreset = (tplId: string) => {
    triggerHaptic('success');
    playTacticalChime('VICTORY');
    const created = createBlueprintFromTemplate(tplId, bioDayId);
    onSaveBlueprints([created, ...blueprints]);
    setSelectedBpId(created.id);
  };

  const handleCreateCustom = () => {
    if (!customName.trim()) return;
    triggerHaptic('success');
    playTacticalChime('VICTORY');
    const created = createCustomSkillBlueprint(
      {
        skillName: customName,
        oracle30DayProof: customOracle,
        zeroStep2Min: customZero,
        analogicalBridge: customAnalogy,
        preMortemSaboteur: customSaboteur,
      },
      bioDayId,
    );
    onSaveBlueprints([created, ...blueprints]);
    setSelectedBpId(created.id);
    setCustomName('');
    setCustomOracle('');
    setCustomZero('');
    setCustomAnalogy('');
    setCustomSaboteur('');
    setShowCustomForm(false);
  };

  const handleToggleStep = (bpId: string, stepId: string) => {
    triggerHaptic('light');
    const next = blueprints.map((bp) => {
      if (bp.id !== bpId) return bp;
      const updatedSteps = bp.steps.map((s) =>
        s.id === stepId ? { ...s, completed: !s.completed } : s,
      ) as SkillBlueprint['steps'];
      return { ...bp, steps: updatedSteps };
    });
    onSaveBlueprints(next);
  };

  const handleDeleteBlueprint = (bpId: string) => {
    triggerHaptic('light');
    onSaveBlueprints(blueprints.filter((b) => b.id !== bpId));
  };

  const handleCreateShieldFromBlueprint = (bp: SkillBlueprint) => {
    if (!onAddIfThen) return;
    triggerHaptic('success');
    onAddIfThen({
      id: `ift_bp_${Date.now()}`,
      triggerSituation: `SE ao estudar "${bp.skillName}" surgir a armadilha: ${bp.preMortemSaboteur.slice(0, 90)}`,
      shieldedAction: `ENTÃO executo imediatamente o Degrau Zero de 2 minutos: ${bp.zeroStep2Min}`,
      machiavelliPreCommitment: 'Material de estudo aberto na véspera e celular fora do alcance.',
      timesTriggered: 0,
      active: true,
    });
    setShieldCreatedId(bp.id);
  };

  const handleRunFeynmanAudit = () => {
    if (!conceptName.trim() && !childExp.trim()) return;
    const res = evaluateFeynmanSocraticAudit({
      conceptName: conceptName.trim() || 'Conceito Fundamental',
      childExplanation: childExp,
      whyAndBoundary: whyBoundary,
      concreteAnalogy: analogyText,
    });
    setAuditResult(res);

    if (res.passed) {
      triggerHaptic('success');
      playTacticalChime('VICTORY');
    } else {
      triggerHaptic('medium');
    }

    const targetBp = blueprints.find((b) => b.id === selectedBpId);
    if (targetBp) {
      const updatedBps = blueprints.map((b) =>
        b.id === targetBp.id
          ? {
              ...b,
              feynmanAuditsCount: b.feynmanAuditsCount + 1,
              bestFeynmanClarityScore: Math.max(b.bestFeynmanClarityScore, res.clarityScorePct),
            }
          : b,
      );
      onSaveBlueprints(updatedBps);
    }

    // Registra sessao estruturada de autoexplicacao com revisao espacada (+3d se passou, +1d se precisa lapidar)
    onSaveDeliberateLog({
      id: `dp_feynman_${Date.now()}`,
      bioDayId,
      timestampMs: Date.now(),
      subSkill: targetBp
        ? `${targetBp.skillName} • ${conceptName.trim() || 'Exame Socrático'}`
        : conceptName.trim() || 'Exame Socrático de Feynman',
      objectiveOracleCriteria: `Auditoria Socrática Chi–Feynman: ${res.clarityScorePct}% de clareza`,
      durationMinutes: 20,
      attemptsCount: 3,
      errorsCount: res.gapsToFix.length,
      feynmanPass: res.passed,
      keyCorrectionNote: res.synthesizedNote,
      nextReviewBioDayId: addDaysToBioDay(bioDayId, res.passed ? 3 : 1),
    });
  };

  return (
    <>
      {/* 1. CONSTRUTOR UNIVERSAL DE HABILIDADES 4C/ID (LUCAS 14:28 + VAN MERRIENBOER) */}
      <div className="card card-amber">
        <div className="section-header">
          <div>
            <div className="section-kicker">
              Construtor Universal 4C/ID • Lucas 14:28 (“Calcular o Custo da Torre”)
            </div>
            <h2 className="section-title">Forjador de Qualquer Habilidade do Zero</h2>
          </div>
          <Compass size={22} color="var(--amber)" />
        </div>

        <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
          Escolha um modelo pronto abaixo em <strong>1 toque</strong> ou decomponha qualquer área
          nova nos <strong>4 Degraus Científicos (Exemplo Resolvido → Sem Cola → Entrelaçado → Prova
          Real)</strong> com Piso de 2 Minutos e Escudo Pré-Morte!
        </p>

        <div className="section-kicker" style={{ marginBottom: 6 }}>
          <Layers size={12} style={{ verticalAlign: 'middle' }} /> Modelos Prontos Do Zero ao Mestre
          (Toque para Ativar)
        </div>
        <div className="chip-row" style={{ marginBottom: 12 }}>
          {PRESET_SKILL_TEMPLATES.map((tpl) => (
            <button
              key={tpl.id}
              type="button"
              className="chip"
              onClick={() => handleAddPreset(tpl.id)}
            >
              <Plus size={12} style={{ verticalAlign: 'middle' }} /> {tpl.skillName.split(' & ')[0]}
            </button>
          ))}
          <button
            type="button"
            className={`chip ${showCustomForm ? 'chip-active' : ''}`}
            onClick={() => setShowCustomForm((v) => !v)}
          >
            <Sparkles size={12} style={{ verticalAlign: 'middle' }} /> Criar Habilidade Própria
          </button>
        </div>

        {showCustomForm && (
          <div
            style={{
              padding: 13,
              borderRadius: 12,
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              marginBottom: 14,
            }}
          >
            <div className="field">
              <label>Qual habilidade você quer dominar partindo do zero?</label>
              <input
                className="input"
                placeholder="Ex.: Eletrônica Digital, Desenho Técnico, Violão, Redação Nota 1000..."
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
              />
            </div>
            <div className="field">
              <label>Prova Real de 30 Dias (o que você fará sem olhar anotações?)</label>
              <input
                className="input"
                placeholder="Ex.: Montar e explicar 3 circuitos funcionando do zero"
                value={customOracle}
                onChange={(e) => setCustomOracle(e.target.value)}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>Degrau Zero de 2 Minutos (dias caóticos)</label>
                <input
                  className="input"
                  placeholder="Ex.: Ler 1 esquema curto e testar 1 componente"
                  value={customZero}
                  onChange={(e) => setCustomZero(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Ponte Analógica (parece com o quê?)</label>
                <input
                  className="input"
                  placeholder="Ex.: Corrente elétrica flui como água em canos"
                  value={customAnalogy}
                  onChange={(e) => setCustomAnalogy(e.target.value)}
                />
              </div>
            </div>
            <div className="field">
              <label>Pré-Morte: maior armadilha que faz iniciantes desistirem</label>
              <input
                className="input"
                placeholder="Ex.: Comprar peças demais e não montar o básico"
                value={customSaboteur}
                onChange={(e) => setCustomSaboteur(e.target.value)}
              />
            </div>
            <button
              type="button"
              className="btn btn-emerald btn-block"
              onClick={handleCreateCustom}
            >
              Construir Torre de Maestria 4C/ID
            </button>
          </div>
        )}

        {blueprints.length === 0 ? (
          <div
            style={{
              padding: 14,
              borderRadius: 12,
              background: 'var(--bg-elevated)',
              textAlign: 'center',
              fontSize: 13,
            }}
            className="muted"
          >
            Nenhuma Torre de Habilidade ativa ainda — toque em qualquer modelo acima (ex:{' '}
            <strong>Programação</strong>, <strong>Inglês</strong>, <strong>Matemática</strong> ou{' '}
            <strong>Oratória</strong>) para gerar seu mapa passo a passo!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {blueprints.map((bp) => {
              const doneSteps = bp.steps.filter((s) => s.completed).length;
              const pct = Math.round((doneSteps / 4) * 100);
              return (
                <div
                  key={bp.id}
                  style={{
                    padding: 14,
                    borderRadius: 14,
                    background: 'var(--bg-elevated)',
                    border:
                      doneSteps === 4
                        ? '1.5px solid var(--emerald)'
                        : '1px solid var(--border-subtle)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: 8,
                    }}
                  >
                    <div>
                      <span className="badge badge-cyan" style={{ marginBottom: 4 }}>
                        {bp.categoryLabel} • {doneSteps}/4 Degraus ({pct}%)
                      </span>
                      {bp.bestFeynmanClarityScore > 0 && (
                        <span
                          className="badge badge-green"
                          style={{ marginLeft: 6, marginBottom: 4 }}
                        >
                          Feynman {bp.bestFeynmanClarityScore}%
                        </span>
                      )}
                      <h3 style={{ margin: '4px 0', fontSize: 15.5 }}>{bp.skillName}</h3>
                    </div>
                    <button
                      type="button"
                      className="chip"
                      style={{ padding: '4px 8px' }}
                      onClick={() => handleDeleteBlueprint(bp.id)}
                      title="Remover plano"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>

                  <div className="progress-track" style={{ margin: '8px 0 10px' }}>
                    <div className="progress-fill" style={{ width: `${pct}%` }} />
                  </div>

                  <div style={{ fontSize: 12.6, lineHeight: 1.5, marginBottom: 8 }}>
                    <strong>Alvo 30 Dias:</strong> {bp.oracle30DayProof}
                  </div>
                  <div
                    style={{
                      padding: '8px 10px',
                      borderRadius: 10,
                      background: 'rgba(16,185,129,0.09)',
                      border: '1px solid rgba(16,185,129,0.28)',
                      fontSize: 12.3,
                      marginBottom: 8,
                    }}
                  >
                    <strong style={{ color: '#34d399' }}>Degrau Zero (2 min):</strong>{' '}
                    {bp.zeroStep2Min}
                  </div>
                  <div className="muted" style={{ fontSize: 12.2, marginBottom: 10 }}>
                    <strong>Ponte Analógica:</strong> {bp.analogicalBridge}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 10 }}>
                    {bp.steps.map((st) => (
                      <label
                        key={st.id}
                        className="check-toggle"
                        style={{ padding: '8px 10px', margin: 0 }}
                      >
                        <input
                          type="checkbox"
                          checked={st.completed}
                          onChange={() => handleToggleStep(bp.id, st.id)}
                        />
                        <div>
                          <strong
                            style={{
                              fontSize: 12.5,
                              color: st.completed ? '#34d399' : 'var(--amber)',
                            }}
                          >
                            {st.stageLabel}
                          </strong>
                          <div
                            className="muted"
                            style={{
                              fontSize: 12.2,
                              textDecoration: st.completed ? 'line-through' : 'none',
                            }}
                          >
                            {st.actionDescription}
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>

                  {onAddIfThen && (
                    <button
                      type="button"
                      className="btn btn-ghost btn-block"
                      style={{ minHeight: 38, fontSize: 12.2 }}
                      onClick={() => handleCreateShieldFromBlueprint(bp)}
                    >
                      <Shield size={14} />{' '}
                      {shieldCreatedId === bp.id
                        ? '✓ Dique Se-Então Ativado no Panteão!'
                        : 'Blindar com Dique Se-Então Automático'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 2. LABORATORIO SOCRATICO CHI-FEYNMAN (AUTOEXPLICACAO AVALIADA 0..100%) */}
      <div className="card card-cyan">
        <div className="section-header">
          <div>
            <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
              Método Chi–Feynman (Bisra et al., 2018 • g = 0,55)
            </div>
            <h2 className="section-title">Exame Socrático de Clareza Real</h2>
          </div>
          <Award size={22} color="var(--cyan)" />
        </div>

        <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
          Feche o livro/vídeo e passe qualquer conceito pelos 3 filtros contra o autoengano. O motor
          calcula seu <strong>Índice de Clareza Socrática (0–100%)</strong> e agenda revisão
          espaçada!
        </p>

        {blueprints.length > 0 && (
          <div className="field">
            <label>Vincular a qual Torre de Habilidade?</label>
            <select
              className="select"
              value={selectedBpId}
              onChange={(e) => setSelectedBpId(e.target.value)}
            >
              <option value="LIVRE">Tema Livre / Geral</option>
              {blueprints.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.skillName}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="field">
          <label>Conceito testado agora (sem olhar anotações)</label>
          <input
            className="input"
            placeholder="Ex.: Juros Compostos, Recursão, Condicional em Inglês, Perdão vs. Confiança..."
            value={conceptName}
            onChange={(e) => setConceptName(e.target.value)}
          />
        </div>

        <div className="field">
          <label>1. Como você explicaria isso para uma criança de 12 anos sem jargão?</label>
          <textarea
            className="textarea"
            rows={2}
            placeholder="Escreva com palavras simples do dia a dia o que esse conceito faz..."
            value={childExp}
            onChange={(e) => setChildExp(e.target.value)}
          />
        </div>

        <div className="field">
          <label>2. POR QUE isso funciona (causa) e em qual limite/erro quebra?</label>
          <textarea
            className="textarea"
            rows={2}
            placeholder="Ex.: Funciona porque... porém falha/quebra quando falta..."
            value={whyBoundary}
            onChange={(e) => setWhyBoundary(e.target.value)}
          />
        </div>

        <div className="field">
          <label>3. Ponte Analógica: isso funciona igual a qual objeto do mundo físico?</label>
          <input
            className="input"
            placeholder="Ex.: Funciona como uma alavanca / semente / filtro porque..."
            value={analogyText}
            onChange={(e) => setAnalogyText(e.target.value)}
          />
        </div>

        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={handleRunFeynmanAudit}
        >
          <Sparkles size={16} /> Auditar Minha Clareza Socrática (0–100%)
        </button>

        {auditResult && (
          <div
            style={{
              marginTop: 14,
              padding: 13,
              borderRadius: 12,
              background: auditResult.passed ? 'var(--emerald-soft)' : 'var(--amber-soft)',
              border: auditResult.passed
                ? '1.5px solid var(--emerald)'
                : '1.5px solid var(--amber)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ fontSize: 14 }}>
                <CheckCircle2 size={15} style={{ verticalAlign: 'middle' }} />{' '}
                {auditResult.verdictTitle}
              </strong>
              <span className="badge badge-green">{auditResult.clarityScorePct}%</span>
            </div>

            {auditResult.strengths.length > 0 && (
              <ul style={{ margin: '8px 0 4px', paddingLeft: 18, fontSize: 12.6 }}>
                {auditResult.strengths.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            )}

            {auditResult.gapsToFix.length > 0 && (
              <div style={{ marginTop: 6, fontSize: 12.5 }}>
                <strong>Ajustes para chegar aos 100%:</strong>
                <ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>
                  {auditResult.gapsToFix.map((g) => (
                    <li key={g}>{g}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};
