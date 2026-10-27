import React, { useState } from 'react'
import {
  OptimizationStats,
  StepTrace,
} from '../types'
import {
  TrendingDown,
  Copy,
  Check,
  Cpu,
  Scissors,
  Zap,
  ListOrdered,
  FileCode,
} from 'lucide-react'

interface ComparisonPanelProps {
  originalCode: string
  optimizedCode: string
  stats?: OptimizationStats
  explanations: string[]
  traces: StepTrace[]
  currentStepIndex: number
  onSelectStep: (index: number) => void
}

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({
  originalCode,
  optimizedCode,
  stats,
  explanations,
  traces,
  currentStepIndex,
  onSelectStep,
}) => {
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'comparison' | 'timeline'>('comparison')

  const handleCopy = () => {
    navigator.clipboard.writeText(optimizedCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const reduction = stats?.reduction_percentage ?? 0
  const isPositiveReduction = reduction > 0

  return (
    <aside className="right-panel">
      {/* 1. Metrics Overview Section */}
      <div className="panel-section">
        <div className="panel-section-title">
          <span>Optimization Metrics</span>
          {stats && (
            <span
              style={{
                color: isPositiveReduction ? '#FF8C52' : '#8AD6D1',
                fontWeight: 700,
                fontSize: '0.8rem',
              }}
            >
              {isPositiveReduction ? `-${reduction}% Instructions` : '0% Change'}
            </span>
          )}
        </div>

        {stats ? (
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-value">
                {stats.original_instruction_count} → {stats.optimized_instruction_count}
              </span>
              <span className="metric-label">Instructions Count</span>
            </div>

            <div className="metric-card">
              <span
                className="metric-value"
                style={{ color: stats.cse_hits > 0 ? '#FF8C52' : '#ffffff' }}
              >
                {stats.cse_hits}
              </span>
              <span className="metric-label">CSE Eliminations</span>
            </div>

            <div className="metric-card">
              <span
                className="metric-value"
                style={{ color: stats.constant_folds > 0 ? '#FFF0C5' : '#ffffff' }}
              >
                {stats.constant_folds}
              </span>
              <span className="metric-label">Constant Folds</span>
            </div>

            <div className="metric-card">
              <span
                className="metric-value"
                style={{ color: stats.dead_nodes_eliminated > 0 ? '#f87171' : '#ffffff' }}
              >
                {stats.dead_nodes_eliminated}
              </span>
              <span className="metric-label">Dead Nodes Pruned</span>
            </div>
          </div>
        ) : (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            Run optimization to calculate compiler metrics.
          </p>
        )}
      </div>

      {/* 2. Tabs Selector (Comparison vs Construction Timeline) */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-color)',
          background: 'rgba(10, 23, 29, 0.5)',
        }}
      >
        <button
          className="btn"
          style={{
            flex: 1,
            borderRadius: 0,
            borderBottom: activeTab === 'comparison' ? '2px solid #359FA0' : 'none',
            background: activeTab === 'comparison' ? 'rgba(53, 159, 160, 0.18)' : 'transparent',
            color: activeTab === 'comparison' ? '#ffffff' : 'var(--text-dim)',
            padding: '10px',
            fontSize: '0.78rem',
          }}
          onClick={() => setActiveTab('comparison')}
        >
          <FileCode size={14} /> Code Diff
        </button>

        <button
          className="btn"
          style={{
            flex: 1,
            borderRadius: 0,
            borderBottom: activeTab === 'timeline' ? '2px solid #359FA0' : 'none',
            background: activeTab === 'timeline' ? 'rgba(53, 159, 160, 0.18)' : 'transparent',
            color: activeTab === 'timeline' ? '#ffffff' : 'var(--text-dim)',
            padding: '10px',
            fontSize: '0.78rem',
          }}
          onClick={() => setActiveTab('timeline')}
        >
          <ListOrdered size={14} /> DAG Trace ({traces.length})
        </button>
      </div>

      {/* 3. Tab Contents */}
      {activeTab === 'comparison' ? (
        <div className="panel-section" style={{ flex: 1 }}>
          <div className="diff-container">
            {/* Original Code */}
            <div className="diff-col">
              <div className="diff-title">Original TAC</div>
              <div className="diff-code-box">
                {originalCode || '// Run optimize to view original'}
              </div>
            </div>

            {/* Optimized Code */}
            <div className="diff-col">
              <div className="diff-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Optimized TAC</span>
                {optimizedCode && (
                  <button
                    onClick={handleCopy}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: copied ? '#34d399' : 'var(--text-muted)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      fontSize: '0.68rem',
                    }}
                    title="Copy optimized code"
                  >
                    {copied ? <Check size={11} /> : <Copy size={11} />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                )}
              </div>
              <div className="diff-code-box optimized">
                {optimizedCode || '// Run optimize to view output'}
              </div>
            </div>
          </div>

          {/* Compiler Explanations */}
          {explanations.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div className="panel-section-title" style={{ marginBottom: 8 }}>
                <span>Compiler Decision Log</span>
              </div>
              <ul style={{ paddingLeft: 18, fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                {explanations.map((exp, idx) => (
                  <li key={idx} style={{ marginBottom: 4 }}>
                    {exp}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        /* Construction Timeline Tab */
        <div className="panel-section" style={{ flex: 1 }}>
          <div className="panel-section-title">
            <span>Step-by-Step Construction Log</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
              Click to jump
            </span>
          </div>

          <div className="timeline-list">
            {traces.map((trace, idx) => {
              const isSelected = idx === currentStepIndex
              const isCse = trace.action_type === 'CSE_HIT'
              const isFold = trace.action_type === 'CONSTANT_FOLD'

              return (
                <div
                  key={idx}
                  className={`timeline-item ${isSelected ? 'active' : ''} ${isCse ? 'cse' : ''} ${isFold ? 'fold' : ''}`}
                  onClick={() => onSelectStep(idx)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                      Step {trace.step_number}: {trace.instruction_text}
                    </span>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        background: 'rgba(255, 255, 255, 0.08)',
                        color: isCse ? '#c084fc' : isFold ? '#fde68a' : '#94a3b8',
                      }}
                    >
                      {trace.action_type}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>
                    {trace.description}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </aside>
  )
}
