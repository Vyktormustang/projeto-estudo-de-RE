import React, { useMemo } from 'react';
import { Moon, Sun, Activity } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface SleepChartProps {
  bioDayId: string;
  vault: VaultState;
}

export const SleepChart: React.FC<SleepChartProps> = ({ bioDayId, vault }) => {
  const last14Days = useMemo(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 14; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const sleepData = useMemo(() => {
    return last14Days.map((d) => {
      const ci = vault.checkIns[d];
      if (!ci) return { date: d, hours: null, label: d.slice(5) };
      return { date: d, hours: ci.sleepHours, label: d.slice(5) };
    });
  }, [last14Days, vault.checkIns]);

  const validData = sleepData.filter((d) => d.hours !== null);
  const avgHours = validData.length > 0
    ? validData.reduce((a, b) => a + (b.hours ?? 0), 0) / validData.length
    : 0;
  const maxHours = validData.length > 0 ? Math.max(...validData.map((d) => d.hours!)) : 0;
  const minHours = validData.length > 0 ? Math.min(...validData.map((d) => d.hours!)) : 0;

  const chartWidth = 340;
  const chartHeight = 90;
  const padding = 30;
  const plotWidth = chartWidth - padding * 2;
  const plotHeight = chartHeight - 20;

  const maxY = Math.max(9, maxHours + 1);

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--amber)' }}>
            Sono nos Últimos 14 Dias
          </div>
          <h2 className="section-title">Horas de Sono</h2>
        </div>
        <Moon size={20} color="var(--amber)" />
      </div>

      <div className="grid-3" style={{ gap: 10, marginBottom: 10 }}>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--amber)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Média</div>
          <div className="metric-value" style={{ fontSize: 20, fontWeight: 900, color: 'var(--amber)' }}>{avgHours > 0 ? avgHours.toFixed(1) : '--'}</div>
          <div className="metric-sub">horas/noite</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--emerald)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Máxima</div>
          <div className="metric-value" style={{ fontSize: 20, fontWeight: 900, color: '#34d399' }}>{maxHours}</div>
          <div className="metric-sub">horas</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--rose)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Dias Registrados</div>
          <div className="metric-value" style={{ fontSize: 20, fontWeight: 900, color: '#ef4444' }}>{validData.length}</div>
          <div className="metric-sub">de 14</div>
        </div>
      </div>

      {/* Gráfico de barras de sono */}
      <div style={{ marginBottom: 8 }}>
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
        >
          {/* Barras de sono */}
          {validData.map((d, i) => {
            const x = padding + (i / Math.max(1, validData.length - 1)) * plotWidth;
            const barWidth = plotWidth / Math.max(1, validData.length) * 0.6;
            const barHeight = ((d.hours! / maxY) * plotHeight);
            const y = 20 + plotHeight - barHeight;
            const isBelowTarget = d.hours! < 7;
            return (
              <rect
                key={d.date}
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                rx={2}
                fill={isBelowTarget ? 'rgba(239, 68, 68, 0.6)' : 'rgba(6, 182, 212, 0.7)'}
              />
            );
          })}

          {/* Linha de meta (7h) */}
          {(() => {
            const targetY = 20 + plotHeight - ((7 / maxY) * plotHeight);
            return (
              <line
                x1={padding}
                y1={targetY}
                x2={chartWidth - padding}
                y2={targetY}
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
            );
          })()}

          {/* Eixo Y */}
          {[3, 6, 9].map((y) => (
            <text
              key={y}
              x={10}
              y={20 + ((maxY - y) / maxY) * plotHeight + 3}
              fill="#64748b"
              fontSize="9"
              textAnchor="end"
            >
              {y}h
            </text>
          ))}

          {/* Eixo X */}
          {validData.filter((_, i) => i % 3 === 0).map((d, i) => {
            const x = padding + (i * 3 / Math.max(1, validData.length - 1)) * plotWidth;
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
        Barras verdes = sono adequado (≥7h) • Barras vermelhas = sono insuficiente (&lt;7h) • Linha tracejada = meta de 7h
      </div>
    </div>
  );
};

export default SleepChart;
