import React, { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { DagNodeData } from '../types'

export const CustomDagNode = memo(({ data }: { data: DagNodeData }) => {
  const isLeaf = data.kind === 'LEAF_VAR' || data.kind === 'LEAF_CONST'
  const isConst = data.kind === 'LEAF_CONST' || data.const_value !== undefined && data.const_value !== null
  const isDead = data.is_dead
  const isReused = data.is_reused
  const isActive = data.isActive

  let opClass = 'op'
  if (data.kind === 'LEAF_VAR') opClass = 'var'
  if (isConst) opClass = 'const'

  return (
    <div
      className={`dag-node-card ${isActive ? 'active' : ''} ${isReused ? 'reused' : ''} ${isDead ? 'dead' : ''}`}
      style={{
        boxShadow: isActive ? '0 0 24px rgba(138, 214, 209, 0.75)' : undefined,
      }}
    >
      {/* Top Handle for incoming edges */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#359FA0', width: 8, height: 8 }}
      />

      <div className="node-header">
        <span style={{ fontWeight: 600 }}>{data.id}</span>
        <span style={{ fontSize: '0.62rem', opacity: 0.8 }}>
          {isConst ? 'CONST' : isLeaf ? 'LEAF' : 'OPERATOR'}
        </span>
      </div>

      <div className="node-body">
        <div className={`node-op ${opClass}`}>
          {isConst ? String(data.const_value ?? data.op) : data.op}
        </div>

        {/* Status badges */}
        <div style={{ display: 'flex', gap: '4px', justifyContent: 'center', marginTop: '4px' }}>
          {isReused && (
            <span
              style={{
                fontSize: '0.62rem',
                background: 'rgba(255, 140, 82, 0.25)',
                color: '#FF8C52',
                border: '1px solid rgba(255, 140, 82, 0.55)',
                padding: '1px 5px',
                borderRadius: '4px',
              }}
            >
              CSE Reused
            </span>
          )}
          {data.is_folded && (
            <span
              style={{
                fontSize: '0.62rem',
                background: 'rgba(255, 240, 197, 0.25)',
                color: '#FFF0C5',
                border: '1px solid rgba(255, 240, 197, 0.55)',
                padding: '1px 5px',
                borderRadius: '4px',
              }}
            >
              Folded
            </span>
          )}
          {data.is_simplified && (
            <span
              style={{
                fontSize: '0.62rem',
                background: 'rgba(138, 214, 209, 0.25)',
                color: '#8AD6D1',
                border: '1px solid rgba(138, 214, 209, 0.55)',
                padding: '1px 5px',
                borderRadius: '4px',
              }}
            >
              Identity
            </span>
          )}
          {isDead && (
            <span
              style={{
                fontSize: '0.62rem',
                background: 'rgba(244, 63, 94, 0.25)',
                color: '#fecdd3',
                border: '1px solid rgba(244, 63, 94, 0.5)',
                padding: '1px 5px',
                borderRadius: '4px',
              }}
            >
              Pruned
            </span>
          )}
        </div>

        {/* Attached Variable Labels */}
        {data.labels && data.labels.length > 0 && (
          <div className="node-labels-badge">
            {data.labels.map((lbl) => (
              <span key={lbl} className="label-tag" title={`Variable ${lbl} bound to this value`}>
                {lbl}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Handle for outgoing edges */}
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#FF8C52', width: 8, height: 8 }}
      />
    </div>
  )
})
