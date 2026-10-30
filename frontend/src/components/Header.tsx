import React from 'react'
import { Zap, Play, BookOpen, RotateCcw, Sparkles } from 'lucide-react'
import { Preset } from '../types'

interface HeaderProps {
  presets: Preset[]
  selectedPresetId: string
  onSelectPreset: (presetId: string) => void
  onRunOptimize: () => void
  onReset: () => void
  onOpenTheory: () => void
  isOptimizing: boolean
}

export const Header: React.FC<HeaderProps> = ({
  presets,
  selectedPresetId,
  onSelectPreset,
  onRunOptimize,
  onReset,
  onOpenTheory,
  isOptimizing,
}) => {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-icon">
          <Zap size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="brand-title">DAGOpt</span>
            <span className="brand-badge">Local Optimizer</span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', margin: 0 }}>
            Interactive Basic-Block DAG Optimizer & Compiler Visualizer
          </p>
        </div>
      </div>

      <div className="header-controls">
        {/* Preset Selector */}
        <select
          className="preset-select"
          value={selectedPresetId}
          onChange={(e) => onSelectPreset(e.target.value)}
          title="Select a predefined textbook compiler example"
        >
          <option value="" disabled>
            Load Textbook Example...
          </option>
          {Array.from(new Set(presets.map((p) => p.category))).map((category) => (
            <optgroup key={category} label={category}>
              {presets
                .filter((p) => p.category === category)
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>

        {/* Reset / Clear Button */}
        <button
          className="btn btn-secondary"
          onClick={onReset}
          title="Reset code and layout"
        >
          <RotateCcw size={15} />
          Reset
        </button>

        {/* Compiler Theory Modal */}
        <button
          className="btn btn-secondary"
          onClick={onOpenTheory}
          title="View Compiler Design & DAG Theory"
        >
          <BookOpen size={15} />
          Theory Guide
        </button>

        {/* Primary Run Optimize Button */}
        <button
          className="btn btn-primary"
          onClick={onRunOptimize}
          disabled={isOptimizing}
          title="Construct DAG and Apply Optimizations"
        >
          {isOptimizing ? (
            <>
              <Sparkles size={16} className="animate-spin" />
              Optimizing...
            </>
          ) : (
            <>
              <Play size={16} fill="currentColor" />
              Optimize Block
            </>
          )}
        </button>
      </div>
    </header>
  )
}
