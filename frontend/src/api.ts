import { OptimizationOptions, OptimizationResult, Preset } from './types'

const BASE_URL = '' // Uses Vite dev proxy

export async function fetchPresets(): Promise<Preset[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/presets`)
    if (!res.ok) throw new Error('Failed to fetch presets')
    const data = await res.json()
    return data.presets
  } catch (err) {
    console.error('Presets error:', err)
    return []
  }
}

export async function optimizeCode(
  code: string,
  options: OptimizationOptions,
  blockId?: string,
  customLiveVars?: string[]
): Promise<OptimizationResult> {
  const payload = {
    code,
    block_id: blockId,
    enable_cse: options.enable_cse,
    enable_constant_folding: options.enable_constant_folding,
    enable_constant_propagation: options.enable_constant_propagation,
    enable_algebraic_simplification: options.enable_algebraic_simplification,
    enable_dead_code_elimination: options.enable_dead_code_elimination,
    custom_live_vars: customLiveVars && customLiveVars.length > 0 ? customLiveVars : null,
  }

  const res = await fetch(`${BASE_URL}/api/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || `Optimization failed (${res.status})`)
  }

  return await res.json()
}
