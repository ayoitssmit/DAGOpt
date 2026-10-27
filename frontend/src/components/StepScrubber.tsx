import React, { useEffect, useState } from 'react'
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  ChevronLeft,
  ChevronRight,
  Info,
} from 'lucide-react'
import { StepTrace } from '../types'

interface StepScrubberProps {
  traces: StepTrace[]
  currentStepIndex: number
  onChangeStep: (index: number) => void
}

export const StepScrubber: React.FC<StepScrubberProps> = ({
  traces,
  currentStepIndex,
  onChangeStep,
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [playSpeed, setPlaySpeed] = useState<number>(1500) // ms per step

  const totalSteps = traces.length
  const currentTrace = traces[currentStepIndex] || traces[totalSteps - 1]

  // Auto-play effect
  useEffect(() => {
    if (!isPlaying) return

    if (currentStepIndex >= totalSteps - 1) {
      setIsPlaying(false)
      return
    }

    const timer = setTimeout(() => {
      onChangeStep(currentStepIndex + 1)
    }, playSpeed)

    return () => clearTimeout(timer)
  }, [isPlaying, currentStepIndex, totalSteps, playSpeed, onChangeStep])

  if (totalSteps === 0) return null

  const handlePrev = () => {
    setIsPlaying(false)
    if (currentStepIndex > 0) onChangeStep(currentStepIndex - 1)
  }

  const handleNext = () => {
    setIsPlaying(false)
    if (currentStepIndex < totalSteps - 1) onChangeStep(currentStepIndex + 1)
  }

  const handleFirst = () => {
    setIsPlaying(false)
    onChangeStep(0)
  }

  const handleLast = () => {
    setIsPlaying(false)
    onChangeStep(totalSteps - 1)
  }

  const togglePlay = () => {
    if (!isPlaying && currentStepIndex >= totalSteps - 1) {
      onChangeStep(0)
    }
    setIsPlaying(!isPlaying)
  }

  return (
    <div className="scrubber-bar">
      <div className="scrubber-controls">
        {/* Playback Buttons */}
        <div className="scrubber-buttons">
          <button
            className="icon-btn"
            onClick={handleFirst}
            disabled={currentStepIndex === 0}
            title="First Step"
          >
            <SkipBack size={15} />
          </button>
          <button
            className="icon-btn"
            onClick={handlePrev}
            disabled={currentStepIndex === 0}
            title="Previous Step"
          >
            <ChevronLeft size={16} />
          </button>
          <button
            className="btn btn-primary"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            onClick={togglePlay}
            title={isPlaying ? 'Pause Construction' : 'Auto Play Step-by-Step'}
          >
            {isPlaying ? (
              <>
                <Pause size={14} fill="currentColor" /> Pause
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" /> Play
              </>
            )}
          </button>
          <button
            className="icon-btn"
            onClick={handleNext}
            disabled={currentStepIndex >= totalSteps - 1}
            title="Next Step"
          >
            <ChevronRight size={16} />
          </button>
          <button
            className="icon-btn"
            onClick={handleLast}
            disabled={currentStepIndex >= totalSteps - 1}
            title="Jump to Final DAG"
          >
            <SkipForward size={15} />
          </button>
        </div>

        {/* Step indicator and speed selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            className="preset-select"
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            value={playSpeed}
            onChange={(e) => setPlaySpeed(Number(e.target.value))}
            title="Playback Speed"
          >
            <option value={2200}>0.5x Speed</option>
            <option value={1500}>1.0x Normal</option>
            <option value={800}>2.0x Fast</option>
          </select>

          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
            Step {currentStepIndex + 1} / {totalSteps}
          </span>
        </div>
      </div>

      {/* Scrub Slider */}
      <input
        type="range"
        className="scrubber-slider"
        min={0}
        max={totalSteps - 1}
        value={currentStepIndex}
        onChange={(e) => {
          setIsPlaying(false)
          onChangeStep(Number(e.target.value))
        }}
      />

      {/* Live Explanation Banner */}
      {currentTrace && (
        <div className="scrubber-ticker">
          <Info size={16} style={{ flexShrink: 0, color: '#38bdf8' }} />
          <div style={{ flex: 1 }}>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                color: '#ffffff',
                marginRight: '8px',
                background: 'rgba(255, 255, 255, 0.1)',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              {currentTrace.instruction_text}
            </span>
            <span>{currentTrace.description}</span>
          </div>
        </div>
      )}
    </div>
  )
}
