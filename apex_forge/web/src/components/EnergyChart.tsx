import React, { useMemo } from 'react';
import { Activity, Flame, Zap, Moon } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface EnergyChartProps {
  bioDayId: string;
  vault: VaultState;
}

export const EnergyChart: React.FC<EnergyChartProps> = ({ bioDayId, vault }) => {
  const last14Days = useMemo(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 14; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const energyData = useMemo(() => {
    return last14Days.map((d) => {
      const ci = vault.checkIns[d];
      if (!ci) return { date: d, energy: null, label: d.slice(5) };
      return { date: d, energy: ci.energyLevel, label: d.slice(5) };
    });
  }, [last14Days, vault.checkIns]);

  const validData = energyData.filter((d) => d.energy !== null);
  const maxEnergy = validData.length > 0 ? Math.max(...validData.map((d) => d.energy!)) : 7;
  const minEnergy = validData.length > 0 ? Math.min(...validData.map((d) => d.energy!)) : 1;
  const avgEnergy = validData.length > 0
    ? validData.reduce((a, b) => a + (b.energy ?? 0), 0) / validData.length
    : 0;

  const chartWidth = 340;
  const chartHeight = 90;
  const padding = 30;
  const plotWidth = chartWidth - padding * 2;
  const plotHeight = chartHeight - 20;

  return (
    <div className="card card-cyan" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
            Energia nos Últimos 14 Dias
          </div>
          <h2 className="section-title">Tendência de Energia</h2>
        </div>
        <Activity size={20} color="var(--cyan)" />
      </div>

      <div className="grid-3" style={{ gap: 10, marginBottom: 10 }}>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--cyan)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Média</div>
          <div className="metric-value" style={{ fontSize: 20, fontWeight: 900, color: 'var(--cyan)' }}>{avgEnergy > 0 ? avgEnergy.toFixed(1) : '--'}</div>
          <div className="metric-sub">/7 energia</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--emerald)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Máxima</div>
          <div className="metric-value" style={{ fontSize: 20, fontWeight: 900, color: '#34d399' }}>{maxEnergy}</div>
          <div className="metric-sub">/7</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--rose)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Dias Registrados</div>
          <div className="metric-value" style={{ fontSize: 20, fontWeight: 900, color: '#ef4444' }}>{validData.length}</div>
          <div className="metric-sub">de 14</div>
        </div>
      </div>

      {/* Gráfico de linha */}
      <div style={{ marginBottom: 8 }}>
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
        >
          {/* Linha de grade */}
          {[1, 3, 5, 7].map((y) => {
            const py = 20 + ((7 - y) / 6) * plotHeight;
            return (
              <line
                key={y}
                x1={padding}
                y1={py}
                x2={chartWidth - padding}
                y2={py}
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="1"
              />
            );
          })}

          {/* Linha de energia */}
          {validData.length > 1 && (
            <polyline
              points={validData
                .map((d, i) => {
                  const x = padding + (i / (validData.length - 1)) * plotWidth;
                  const y = 20 + ((7 - d.energy!) / 6) * plotHeight;
                  return `${x.toFixed(1)},${y.toFixed(1)}`;
                })
                .join(' ')}
              fill="none"
              stroke="#22d3ee"
              strokeWidth="2"
            />
          )}

          {/* Pontos de dados */}
          {validData.map((d, i) => {
            const x = padding + (i / (validData.length - 1)) * plotWidth;
            const y = 20 + ((7 - d.energy!) / 6) * plotHeight;
            return (
              <circle
                key={d.date}
                cx={x}
                cy={y}
                r={3}
                fill="#22d3ee"
                stroke="#0f172a"
                strokeWidth="1"
              />
            );
          })}

          {/* Eixo Y */}
          {[7, 5, 3, 1].map((y) => (
            <text
              key={y}
              x={10}
              y={20 + ((7 - y) / 6) * plotHeight + 3}
              fill="#64748b"
              fontSize="9"
              textAnchor="end"
            >
              {y}
            </text>
          ))}

          {/* Eixo X - mostrar a cada 3 dias */}
          {validData.filter((_, i) => i % 3 === 0).map((d, i) => {
            const x = padding + (i * 3 / (validData.length - 1)) * plotWidth;
            return (
              <text
                key={d.date}
                x={x}
                y={chartHeight - 5}
                fill="#64748b"
                fontSize="8"
                textAnchor="middle"
              >
                {d.label}
              </text>
            );
          })}
        </svg>
      </div>

      <div style={{ fontSize: 11, color: 'var(--text-secondary)', textAlign: 'center' }}>
        Linha azul = nível de energia (1-7) por dia com check-in registrado
      </div>
    </div>
  );
};

export default EnergyChart;
