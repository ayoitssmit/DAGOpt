import React from 'react'
import { BasicBlockInfo, OptimizationOptions } from '../types'
import { Sliders, Code2, Layers, CheckCircle2 } from 'lucide-react'

interface CodeEditorProps {
  code: string
  onChangeCode: (code: string) => void
  blocks: BasicBlockInfo[]
  activeBlockId: string
  onSelectBlock: (blockId: string) => void
  options: OptimizationOptions
  onChangeOptions: (options: OptimizationOptions) => void
  availableVars: string[]
  liveOutVars: string[]
  onToggleLiveVar: (varName: string) => void
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  onChangeCode,
  blocks,
  activeBlockId,
  onSelectBlock,
  options,
  onChangeOptions,
  availableVars,
  liveOutVars,
  onToggleLiveVar,
}) => {
  const lineCount = Math.max(1, code.split('\n').length)
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1)

  const handleToggleOption = (key: keyof OptimizationOptions) => {
    onChangeOptions({
      ...options,
      [key]: !options[key],
    })
  }

  return (
    <aside className="left-panel">
      {/* 1. Code Input Section */}
      <div className="panel-section">
        <div className="panel-section-title">
          <span>
            <Code2 size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
            Three-Address Code (TAC)
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{lineCount} lines</span>
        </div>

        <div className="code-editor-container">
          <div className="code-editor-gutter">
            {lineNumbers.map((n) => (
              <div key={n}>{n}</div>
            ))}
          </div>
          <textarea
            className="code-editor-textarea"
            value={code}
            onChange={(e) => onChangeCode(e.target.value)}
            placeholder="e.g.&#10;a = b + c&#10;d = b + c&#10;e = a * d"
            spellCheck={false}
          />
        </div>

        {/* Basic Blocks Partitioning Display */}
        {blocks.length > 1 && (
          <div style={{ marginTop: 12 }}>
            <div className="panel-section-title" style={{ marginBottom: 6 }}>
              <span>
                <Layers size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
                Detected Basic Blocks ({blocks.length})
              </span>
            </div>
            <div className="block-chips">
              {blocks.map((b) => (
                <button
                  key={b.id}
                  className={`block-chip ${b.id === activeBlockId ? 'active' : ''}`}
                  onClick={() => onSelectBlock(b.id)}
                  title={`Block ${b.name}: lines ${b.start_line}-${b.end_line} (${b.instruction_count} instructions)`}
                >
                  {b.name} ({b.instruction_count} insts)
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 2. Optimization Passes Configuration */}
      <div className="panel-section">
        <div className="panel-section-title">
          <span>
            <Sliders size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
            Optimization Passes
          </span>
        </div>

        {/* CSE */}
        <label className="option-toggle">
          <div className="option-info">
            <span className="option-label">Common Subexpression Elimination</span>
            <span className="option-desc">Reuse computed DAG nodes for identical expressions</span>
          </div>
          <div className="switch">
            <input
              type="checkbox"
              checked={options.enable_cse}
              onChange={() => handleToggleOption('enable_cse')}
            />
            <span className="slider" />
          </div>
        </label>

        {/* Constant Folding */}
        <label className="option-toggle">
          <div className="option-info">
            <span className="option-label">Constant Folding</span>
            <span className="option-desc">Evaluate compile-time constant arithmetic (e.g. 10 + 20)</span>
          </div>
          <div className="switch">
            <input
              type="checkbox"
              checked={options.enable_constant_folding}
              onChange={() => handleToggleOption('enable_constant_folding')}
            />
            <span className="slider" />
          </div>
        </label>

        {/* Constant Propagation */}
        <label className="option-toggle">
          <div className="option-info">
            <span className="option-label">Constant Propagation</span>
            <span className="option-desc">Forward known constant values to subsequent uses</span>
          </div>
          <div className="switch">
            <input
              type="checkbox"
              checked={options.enable_constant_propagation}
              onChange={() => handleToggleOption('enable_constant_propagation')}
            />
            <span className="slider" />
          </div>
        </label>

        {/* Algebraic Simplification */}
        <label className="option-toggle">
          <div className="option-info">
            <span className="option-label">Algebraic Identities</span>
            <span className="option-desc">Simplify x + 0, x * 1, x * 0, x - x, x ^ 0</span>
          </div>
          <div className="switch">
            <input
              type="checkbox"
              checked={options.enable_algebraic_simplification}
              onChange={() => handleToggleOption('enable_algebraic_simplification')}
            />
            <span className="slider" />
          </div>
        </label>

        {/* Dead Code Elimination */}
        <label className="option-toggle">
          <div className="option-info">
            <span className="option-label">Dead Code Elimination</span>
            <span className="option-desc">Prune DAG nodes with no live-out dependents</span>
          </div>
          <div className="switch">
            <input
              type="checkbox"
              checked={options.enable_dead_code_elimination}
              onChange={() => handleToggleOption('enable_dead_code_elimination')}
            />
            <span className="slider" />
          </div>
        </label>
      </div>

      {/* 3. Live-Out Variables Management */}
      <div className="panel-section">
        <div className="panel-section-title">
          <span>
            <CheckCircle2 size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
            Live Variables at Exit
          </span>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>Click to toggle</span>
        </div>
        <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6 }}>
          Variables considered needed outside this basic block. Dead code analysis preserves only values needed to compute these:
        </p>
        <div className="live-vars-container">
          {availableVars.length === 0 && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              No variables detected yet. Run optimization to analyze.
            </span>
          )}
          {availableVars.map((v) => {
            const isLive = liveOutVars.includes(v)
            return (
              <button
                key={v}
                className={`var-pill ${isLive ? 'active' : ''}`}
                onClick={() => onToggleLiveVar(v)}
                title={isLive ? `Variable '${v}' is LIVE (needed at exit)` : `Variable '${v}' is DEAD (can be pruned)`}
              >
                {v} {isLive ? '✓' : ''}
              </button>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
