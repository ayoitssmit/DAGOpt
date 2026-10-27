import React, { useEffect } from 'react'
import { X, BookOpen, GitMerge, Cpu, Trash2, ArrowRight } from 'lucide-react'

interface TheoryModalProps {
  isOpen: boolean
  onClose: () => void
}

export const TheoryModal: React.FC<TheoryModalProps> = ({ isOpen, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <BookOpen size={20} color="#FF8C52" />
            <h2 style={{ fontSize: '1.15rem', color: '#ffffff', margin: 0 }}>
              Compiler Design Theory: DAG-Based Local Optimization
            </h2>
          </div>
          <button
            className="icon-btn"
            onClick={onClose}
            title="Close Guide (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <h3>1. What is a Basic Block?</h3>
          <p>
            In compiler design, a <strong>basic block</strong> is a sequence of straight-line Three-Address Code instructions with:
          </p>
          <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
            <li>A single entry point: execution enters only at the first instruction.</li>
            <li>No branches or jumps within the block (except possibly at the exit).</li>
          </ul>
          <p>
            Because execution cannot branch into or out of the middle of a basic block, we can safely reorder, simplify, and eliminate redundant calculations locally.
          </p>

          <h3>2. What is a DAG Representation?</h3>
          <p>
            A <strong>Directed Acyclic Graph (DAG)</strong> represents the flow of computed values within a basic block:
          </p>
          <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
            <li><strong>Leaf Nodes:</strong> Represent the initial values of variables or compile-time constants upon entering the block.</li>
            <li><strong>Interior Nodes:</strong> Represent operator applications (e.g. <code>+</code>, <code>*</code>, <code>[]</code>) whose children are the operands.</li>
            <li><strong>Variable Labels:</strong> A node maintains a list of variable names whose current value is computed by that node. If variable <code>a</code> is reassigned, its label is detached from the old node and attached to the new node.</li>
          </ul>

          <h3>3. Value Numbering & Common Subexpression Elimination (CSE)</h3>
          <p>
            When processing an expression <code>dst = x op y</code>, the compiler checks if an interior node with operator <code>op</code> and children <code>(node(x), node(y))</code> already exists:
          </p>
          <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
            <li>If it exists, the compiler does <em>not</em> emit a duplicate computation. Instead, it reuses the existing DAG node and attaches <code>dst</code> to its label list!</li>
            <li>For commutative operators (e.g. <code>+</code>, <code>*</code>, <code>==</code>, <code>&</code>), both <code>(x, y)</code> and <code>(y, x)</code> match the same node.</li>
          </ul>

          <h3>4. Constant Folding & Propagation</h3>
          <p>
            If both operand children of an operation are compile-time constants (e.g. <code>10 + 20</code>), the compiler evaluates the operation at compile time and creates or points to a constant node <code>30</code>.
            This value is propagated automatically to any subsequent instruction reading it.
          </p>

          <h3>5. Algebraic Simplification</h3>
          <p>
            Mathematical identities allow eliminating operations without emitting instructions:
          </p>
          <ul style={{ paddingLeft: 20, marginBottom: 12 }}>
            <li><code>x + 0 ⇒ x</code> and <code>0 + x ⇒ x</code></li>
            <li><code>x * 1 ⇒ x</code> and <code>1 * x ⇒ x</code></li>
            <li><code>x * 0 ⇒ 0</code> and <code>0 * x ⇒ 0</code></li>
            <li><code>x - x ⇒ 0</code> and <code>x / 1 ⇒ x</code></li>
          </ul>

          <h3>6. Dead Code Elimination (DCE)</h3>
          <p>
            Any node in the DAG whose computed value is neither needed at the exit of the basic block (not in <em>live-out</em>) nor used as an operand for a live instruction is marked dead and pruned.
          </p>

          <h3>7. Code Generation from the DAG</h3>
          <p>
            To regenerate optimized Three-Address Code, the compiler performs a topological sort on the active DAG nodes (evaluating children before parents). For each interior node, it picks a primary variable, emits the calculation, and emits simple copies for any other variables sharing that value.
          </p>
        </div>
      </div>
    </div>
  )
}
