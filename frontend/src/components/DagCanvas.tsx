import React, { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  BackgroundVariant,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react'
import dagre from 'dagre'
import { CustomDagNode } from './CustomDagNode'
import { DagNodeData, DagEdgeData } from '../types'
import { ArrowDownUp, Maximize2 } from 'lucide-react'

const nodeTypes = {
  customDagNode: CustomDagNode,
}

interface DagCanvasProps {
  nodesData: DagNodeData[]
  edgesData: DagEdgeData[]
  activeNodeId?: string | null
  layoutDirection: 'TB' | 'BT'
  onToggleLayoutDirection: () => void
}

const NODE_WIDTH = 150
const NODE_HEIGHT = 85

function getLayoutedElements(
  nodes: DagNodeData[],
  edges: DagEdgeData[],
  direction: 'TB' | 'BT' = 'TB',
  activeNodeId?: string | null
) {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 40,
    ranksep: 60,
  })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  })

  edges.forEach((edge) => {
    // In compiler DAG: interior operator depends on its children.
    // Parent node -> Child node
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  const layoutedNodes: Node[] = nodes.map((node) => {
    const nodeWithPos = dagreGraph.node(node.id) || { x: 0, y: 0 }
    return {
      id: node.id,
      type: 'customDagNode',
      position: {
        x: nodeWithPos.x - NODE_WIDTH / 2,
        y: nodeWithPos.y - NODE_HEIGHT / 2,
      },
      data: {
        ...node,
        isActive: node.id === activeNodeId,
      },
    }
  })

  const layoutedEdges: Edge[] = edges.map((edge) => {
    const isDead = edge.is_dead
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label || undefined,
      type: 'bezier',
      animated: !isDead,
      style: {
        stroke: isDead ? '#f43f5e' : edge.source === activeNodeId ? '#8AD6D1' : '#359FA0',
        strokeWidth: edge.source === activeNodeId ? 2.5 : 1.8,
        strokeDasharray: isDead ? '4 4' : undefined,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isDead ? '#f43f5e' : edge.source === activeNodeId ? '#8AD6D1' : '#359FA0',
        width: 16,
        height: 16,
      },
    }
  })

  return { nodes: layoutedNodes, edges: layoutedEdges }
}

const FlowInner: React.FC<DagCanvasProps> = ({
  nodesData,
  edgesData,
  activeNodeId,
  layoutDirection,
  onToggleLayoutDirection,
}) => {
  const { fitView } = useReactFlow()

  const { nodes, edges } = useMemo(
    () => getLayoutedElements(nodesData, edgesData, layoutDirection, activeNodeId),
    [nodesData, edgesData, layoutDirection, activeNodeId]
  )

  const handleFitView = useCallback(() => {
    fitView({ padding: 0.2, duration: 400 })
  }, [fitView])

  return (
    <div className="flow-container">
      {/* Top Floating Toolbar */}
      <div className="canvas-toolbar">
        <button
          className="btn btn-secondary"
          style={{ padding: '4px 8px', fontSize: '0.75rem' }}
          onClick={handleFitView}
          title="Fit graph to view"
        >
          <Maximize2 size={13} /> Fit View
        </button>

        <button
          className="btn btn-secondary"
          style={{ padding: '4px 8px', fontSize: '0.75rem' }}
          onClick={onToggleLayoutDirection}
          title="Toggle layout direction"
        >
          <ArrowDownUp size={13} /> {layoutDirection === 'TB' ? 'Roots Top' : 'Leaves Top'}
        </button>

        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginLeft: '6px' }}>
          {nodesData.length} nodes · {edgesData.length} edges
        </span>
      </div>

      {/* Canvas Color Legend */}
      <div className="canvas-legend">
        <div className="legend-item">
          <span className="legend-dot op" /> Operator
        </div>
        <div className="legend-item">
          <span className="legend-dot leaf" /> Variable Leaf
        </div>
        <div className="legend-item">
          <span className="legend-dot const" /> Constant
        </div>
        <div className="legend-item">
          <span className="legend-dot cse" /> CSE Shared
        </div>
        <div className="legend-item">
          <span className="legend-dot dead" /> Pruned (Dead)
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="rgba(255, 240, 197, 0.16)" />
        <Controls
          showInteractive={false}
          style={{
            bottom: 20,
            left: 20,
            background: 'rgba(17, 23, 38, 0.85)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            fill: '#ffffff',
          }}
        />
      </ReactFlow>
    </div>
  )
}

export const DagCanvas: React.FC<DagCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <FlowInner {...props} />
    </ReactFlowProvider>
  )
}
