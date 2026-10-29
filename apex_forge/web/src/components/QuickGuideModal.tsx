import React from 'react';
import { BookOpen, Brain, CheckCircle2, Dumbbell, HelpCircle, Shield, X } from 'lucide-react';

interface Props {
  onClose: () => void;
}

export const QuickGuideModal: React.FC<Props> = ({ onClose }) => {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="section-header">
          <div>
            <div className="section-kicker">Guia Rápido • Linguagem Simples</div>
            <h2 className="section-title">Como Usar a FORJA em 3 Passos</h2>
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

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
          <div className="metric-box" style={{ borderLeft: '3px solid var(--amber)' }}>
            <div style={{ fontWeight: 800, fontSize: 14 }}>
              1. Leia Seu Dia em 20 Segundos (Aba Início)
            </div>
            <div className="muted" style={{ marginTop: 3 }}>
              Informe como dormiu, sua energia e se tem alguma dor. O motor ajusta o treino do dia
              automaticamente — se você dormiu mal ou está com dor no ombro, ele protege você na
              hora!
            </div>
          </div>

          <div className="metric-box" style={{ borderLeft: '3px solid var(--emerald)' }}>
            <div style={{ fontWeight: 800, fontSize: 14 }}>
              <Dumbbell size={14} style={{ verticalAlign: 'middle' }} /> 2. Treine Vendo a
              Demonstração Animada (Aba Treino)
            </div>
            <div className="muted" style={{ marginTop: 3 }}>
              Toque em <strong>“Ver Demonstração”</strong> em qualquer exercício para assistir ao
              movimento animado em tempo real, ver a dica simples de postura e usar os modos de{' '}
              <strong>5 ou 15 minutos</strong> quando o dia estiver corrido.
            </div>
          </div>

          <div className="metric-box" style={{ borderLeft: '3px solid var(--cyan)' }}>
            <div style={{ fontWeight: 800, fontSize: 14 }}>
              <Brain size={14} style={{ verticalAlign: 'middle' }} /> 3. Bicentenário 200 Lições,
              9 Esportes Mentais, Xadrez Chess.com 2.0 &amp; Radar 10D
            </div>
            <div className="muted" style={{ marginTop: 3 }}>
              Domine <strong>Jesus Cristo</strong>, a <strong>Sabedoria Bíblica</strong> e a ciência
              em <strong>10 Pilares × 20 Lições (200 Lições: 50 por Grau)</strong>, jogue{' '}
              <strong>9 esportes mentais</strong> + a aba <strong>♟️ Xadrez Chess.com 2.0</strong>{' '}
              (Clássico FIDE + <strong>Chess960 #0–#959</strong>, 8 Bots 400–2400 Elo, Revisão CAPS %,{' '}
              <strong>36 Problemas + Puzzle Rush</strong>, <strong>Visão 30s</strong>,{' '}
              <strong>8 Finais vs Motor</strong>, <strong>6 Aulas Guiadas</strong> e 49 Aberturas ECO)!
            </div>
          </div>
        </div>

        <div className="section-kicker" style={{ marginBottom: 8 }}>
          <BookOpen size={12} style={{ verticalAlign: 'middle' }} /> Dicionário Sem Complicação
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
          {[
            {
              term: 'Reserva (RIR — Repetições na Reserva)',
              meaning:
                'Quantas repetições você ainda conseguiria fazer antes de travar. Exemplo: "Reserva 2" significa parar quando sentir que só aguentaria mais 2 repetições limpas. Isso gera ganho máximo sem lesionar!',
            },
            {
              term: 'Sinal Verde / Amarelo / Vermelho',
              meaning:
                'Verde = corpo pronto para evoluir; Amarelo = treino moderado e inteligente; Vermelho = recuperação ativa (forçar no Vermelho atrasa seus resultados).',
            },
            {
              term: 'Piso de 5 Minutos & Pivô de 15 Minutos',
              meaning:
                'Nos dias caóticos, nunca faça zero! Fazer 5 ou 15 minutos mantém o hábito vivo no cérebro sem culpa.',
            },
            {
              term: 'Palácio da Memória (Método de Loci)',
              meaning:
                'Técnica comprovada em neuroimagem onde você espalha palavras/conceitos por cômodos imaginários, multiplicando sua capacidade de lembrar.',
            },
            {
              term: 'Dique Se-Então & Mark N+1',
              meaning:
                'Combinar antes o que você fará quando bater preguiça ("Se acontecer X, então faço Y") e tratar qualquer tropeço como ajuste técnico, nunca como derrota.',
            },
          ].map((g) => (
            <div
              key={g.term}
              style={{
                padding: '9px 11px',
                borderRadius: 10,
                background: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: 12.8, color: 'var(--amber)' }}>
                <HelpCircle size={12} style={{ verticalAlign: 'middle' }} /> {g.term}
              </div>
              <div className="muted" style={{ fontSize: 12.4, marginTop: 2 }}>
                {g.meaning}
              </div>
            </div>
          ))}
        </div>

        <button type="button" className="btn btn-emerald btn-block" onClick={onClose}>
          <CheckCircle2 size={16} /> Tudo Claro — Vamos Começar!
        </button>
      </div>
    </div>
  );
};
