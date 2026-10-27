import React, { useState, useEffect, useCallback } from 'react'
import { Header } from './components/Header'
import { CodeEditor } from './components/CodeEditor'
import { DagCanvas } from './components/DagCanvas'
import { StepScrubber } from './components/StepScrubber'
import { ComparisonPanel } from './components/ComparisonPanel'
import { TheoryModal } from './components/TheoryModal'
import {
  BasicBlockInfo,
  OptimizationOptions,
  OptimizationResult,
  Preset,
  DagNodeData,
  DagEdgeData,
} from './types'
import { fetchPresets, optimizeCode } from './api'
import { AlertCircle } from 'lucide-react'

const DEFAULT_CODE = `a = b + c
d = b + c
e = a * d`

export function App() {
  const [presets, setPresets] = useState<Preset[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState<string>('classic_cse')
  const [code, setCode] = useState<string>(DEFAULT_CODE)

  const [blocks, setBlocks] = useState<BasicBlockInfo[]>([])
  const [activeBlockId, setActiveBlockId] = useState<string>('B1')

  const [options, setOptions] = useState<OptimizationOptions>({
    enable_cse: true,
    enable_constant_folding: true,
    enable_constant_propagation: true,
    enable_algebraic_simplification: true,
    enable_dead_code_elimination: true,
  })

  const [availableVars, setAvailableVars] = useState<string[]>([])
  const [liveOutVars, setLiveOutVars] = useState<string[]>([])

  const [result, setResult] = useState<OptimizationResult | null>(null)
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0)
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'BT'>('TB')

  const [isTheoryOpen, setIsTheoryOpen] = useState(false)
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // 1. Fetch presets on mount
  useEffect(() => {
    fetchPresets().then((loadedPresets) => {
      setPresets(loadedPresets)
      if (loadedPresets.length > 0) {
        const first = loadedPresets[0]
        setSelectedPresetId(first.id)
        setCode(first.code)
      }
    })
  }, [])

  // 2. Optimization runner
  const handleRunOptimize = useCallback(
    async (
      overrideCode?: string,
      overrideBlockId?: string,
      overrideLiveVars?: string[]
    ) => {
      const targetCode = overrideCode !== undefined ? overrideCode : code
      const targetBlock = overrideBlockId !== undefined ? overrideBlockId : activeBlockId
      const targetLive = overrideLiveVars !== undefined ? overrideLiveVars : liveOutVars

      setIsOptimizing(true)
      setErrorMessage(null)

      try {
        const data = await optimizeCode(
          targetCode,
          options,
          targetBlock,
          targetLive.length > 0 ? targetLive : undefined
        )
        setResult(data)
        setBlocks(data.basic_blocks)
        setActiveBlockId(data.active_block)
        setAvailableVars(data.available_vars)
        setLiveOutVars(data.live_out)

        // Set scrubber to the final completed step by default
        if (data.step_traces && data.step_traces.length > 0) {
          setCurrentStepIndex(data.step_traces.length - 1)
        }
      } catch (err: any) {
        console.error('Optimization error:', err)
        setErrorMessage(err.message || 'An error occurred during optimization.')
      } finally {
        setIsOptimizing(false)
      }
    },
    [code, activeBlockId, liveOutVars, options]
  )

  // 3. Trigger initial optimization once presets load or code initializes
  useEffect(() => {
    handleRunOptimize(DEFAULT_CODE)
  }, [])

  // Preset switch
  const handleSelectPreset = (presetId: string) => {
    const preset = presets.find((p) => p.id === presetId)
    if (preset) {
      setSelectedPresetId(presetId)
      setCode(preset.code)
      handleRunOptimize(preset.code, 'B1', [])
    }
  }

  // Reset
  const handleReset = () => {
    setCode(DEFAULT_CODE)
    setSelectedPresetId('classic_cse')
    handleRunOptimize(DEFAULT_CODE, 'B1', [])
  }

  // Toggle variable live-out status
  const handleToggleLiveVar = (varName: string) => {
    const updated = liveOutVars.includes(varName)
      ? liveOutVars.filter((v) => v !== varName)
      : [...liveOutVars, varName]
    setLiveOutVars(updated)
    handleRunOptimize(code, activeBlockId, updated)
  }

  // Determine which DAG snapshot to display (scrubber snapshot or final DAG)
  const totalSteps = result?.step_traces.length ?? 0
  const isScrubbingIntermediate = totalSteps > 0 && currentStepIndex < totalSteps - 1
  const currentTrace = result?.step_traces[currentStepIndex]

  const activeNodesData: DagNodeData[] = isScrubbingIntermediate && currentTrace
    ? currentTrace.nodes_snapshot
    : result?.dag_nodes ?? []

  const activeEdgesData: DagEdgeData[] = isScrubbingIntermediate && currentTrace
    ? currentTrace.edges_snapshot
    : result?.dag_edges ?? []

  const activeNodeId = currentTrace?.active_node_id ?? null

  return (
    <div className="app-container">
      {/* Top Navigation & Controls Header */}
      <Header
        presets={presets}
        selectedPresetId={selectedPresetId}
        onSelectPreset={handleSelectPreset}
        onRunOptimize={() => handleRunOptimize()}
        onReset={handleReset}
        onOpenTheory={() => setIsTheoryOpen(true)}
        isOptimizing={isOptimizing}
      />

      {/* Error alert toast if any */}
      {errorMessage && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            padding: '8px 24px',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <AlertCircle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main 3-Column Interactive Workspace */}
      <main className="main-workspace">
        {/* Left Column: Code Editor & Configuration */}
        <CodeEditor
          code={code}
          onChangeCode={(newCode) => {
            setCode(newCode)
          }}
          blocks={blocks}
          activeBlockId={activeBlockId}
          onSelectBlock={(blockId) => {
            setActiveBlockId(blockId)
            handleRunOptimize(code, blockId)
          }}
          options={options}
          onChangeOptions={(newOptions) => {
            setOptions(newOptions)
            // Re-run with new options
            setTimeout(() => handleRunOptimize(), 0)
          }}
          availableVars={availableVars}
          liveOutVars={liveOutVars}
          onToggleLiveVar={handleToggleLiveVar}
        />

        {/* Center Column: Interactive DAG Canvas & Step-Through Player */}
        <section className="center-panel">
          <DagCanvas
            nodesData={activeNodesData}
            edgesData={activeEdgesData}
            activeNodeId={activeNodeId}
            layoutDirection={layoutDirection}
            onToggleLayoutDirection={() =>
              setLayoutDirection((prev) => (prev === 'TB' ? 'BT' : 'TB'))
            }
          />

          {/* Interactive Step-by-Step Construction Scrubber */}
          {result && result.step_traces.length > 0 && (
            <StepScrubber
              traces={result.step_traces}
              currentStepIndex={currentStepIndex}
              onChangeStep={setCurrentStepIndex}
            />
          )}
        </section>

        {/* Right Column: Comparison, Metrics, and Decision Log */}
        <ComparisonPanel
          originalCode={result?.original_code ?? code}
          optimizedCode={result?.optimized_code ?? ''}
          stats={result?.stats}
          explanations={result?.explanations ?? []}
          traces={result?.step_traces ?? []}
          currentStepIndex={currentStepIndex}
          onSelectStep={setCurrentStepIndex}
        />
      </main>

      {/* Theory Guide Modal for Professor Presentation */}
      <TheoryModal isOpen={isTheoryOpen} onClose={() => setIsTheoryOpen(false)} />
    </div>
  )
}
export default App
