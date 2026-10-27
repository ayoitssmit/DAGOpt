export interface DagNodeData {
  id: string
  kind: 'LEAF_VAR' | 'LEAF_CONST' | 'INTERIOR_OP' | 'ARRAY_OP'
  op: string
  children: string[]
  labels: string[]
  const_value?: number | string | boolean | null
  is_reused: boolean
  is_folded: boolean
  is_simplified: boolean
  is_dead: boolean
  creation_reason: string
  isActive?: boolean
}

export interface DagEdgeData {
  id: string
  source: string
  target: string
  label?: string
  is_dead?: boolean
}

export interface StepTrace {
  step_number: number
  instruction_index: number
  instruction_text: string
  action_type: string
  description: string
  active_node_id?: string | null
  reused_node_id?: string | null
  folded_node_id?: string | null
  nodes_snapshot: DagNodeData[]
  edges_snapshot: DagEdgeData[]
  var_table_snapshot: Record<string, string>
}

export interface BasicBlockInfo {
  id: string
  name: string
  start_line: number
  end_line: number
  instruction_count: number
}

export interface OptimizationStats {
  original_instruction_count: number
  optimized_instruction_count: number
  instructions_saved: number
  reduction_percentage: number
  cse_hits: number
  constant_folds: number
  algebraic_simplifications: number
  dead_nodes_eliminated: number
  total_dag_nodes: number
  total_dag_edges: number
}

export interface OptimizationResult {
  success: boolean
  basic_blocks: BasicBlockInfo[]
  active_block: string
  original_code: string
  original_instructions: string[]
  optimized_code: string
  optimized_instructions: string[]
  dag_nodes: DagNodeData[]
  dag_edges: DagEdgeData[]
  step_traces: StepTrace[]
  var_table: Record<string, string>
  live_out: string[]
  available_vars: string[]
  stats: OptimizationStats
  explanations: string[]
}

export interface OptimizationOptions {
  enable_cse: boolean
  enable_constant_folding: boolean
  enable_constant_propagation: boolean
  enable_algebraic_simplification: boolean
  enable_dead_code_elimination: boolean
}

export interface Preset {
  id: string
  title: string
  category: string
  description: string
  code: string
}
