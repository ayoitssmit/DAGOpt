# DAGOpt: Interactive DAG-Based Local Code Optimizer

## 1. Overview

In compiler design, code optimization can be performed at multiple scopes: local, loop, global, and interprocedural. Local optimization focuses strictly on improvements within a single **basic block**—a sequence of consecutive three-address instructions that possesses a single entry point and no internal branching.

A **Directed Acyclic Graph (DAG)** is the foundational data structure used by optimizing compilers to represent the computation flow within a basic block. Rather than constructing redundant operations for repeated expressions, a DAG maps repeated subexpressions to existing computation nodes. This enables automatic common subexpression elimination, constant folding, constant propagation, algebraic simplification, and dead code elimination prior to generating target instructions.

**DAGOpt** is an interactive compiler optimization workbench. It pairs a complete Python compiler engine implementing the classic Aho-Lam-Sethi-Ullman (Dragon Book) algorithms with a modern React and React Flow graphical user interface.

---

## 2. Theoretical Principles

### 2.1 Basic Block Formulation
A sequence of three-address statements forms a basic block if:
1. Control enters the sequence exclusively through its first statement.
2. Control leaves the sequence exclusively through its last statement (no halts or internal jumps).

Basic blocks are partitioned by identifying **leaders**:
- The first statement of the intermediate representation.
- Any statement that is the target of a conditional or unconditional branch (labels).
- Any statement immediately following a conditional or unconditional branch.

### 2.2 DAG Node Semantics
A basic block DAG consists of:
- **Leaf Nodes:** Represent the initial values of variables entering the block or literal constant values.
- **Interior Nodes:** Represent arithmetic, relational, or bitwise operators applied to the values produced by child nodes.
- **Variable Labels:** Each node maintains a list of variable names whose current run-time values are held by that node. If variable `x` is reassigned during block processing, `x` is detached from its previous node and bound to the newly evaluated node.
- **Value Numbering:** Before creating a new interior node for operation `x op y`, the compiler consults a hash table of existing nodes. If a node computing `op(left, right)` already exists, the compiler reuses that node instead of allocating a duplicate. Commutative operators (`+`, `*`, `&`, `|`, `^`, `==`, `!=`) check both operand orderings `(x, y)` and `(y, x)`.

---

## 3. Implemented Optimization Techniques

### 3.1 Common Subexpression Elimination (CSE)
When the compiler encounters an instruction `dst = x op y`:
- If an interior node with operator `op` and children `node(x)` and `node(y)` already exists, no new node is created.
- `dst` is appended to the label list of the existing node.
- Any subsequent instruction referencing `dst` references the precomputed value.

### 3.2 Constant Folding and Propagation
- If both operand nodes `node(x)` and `node(y)` possess known compile-time constant values, the operation is computed at compile time.
- A constant leaf node containing the folded result is created or reused.
- The destination variable is bound directly to this constant node, propagating the constant to downstream calculations.

### 3.3 Algebraic Identities and Simplifications
The optimizer evaluates standard arithmetic and bitwise identities prior to node allocation:
- Additive Identity: `x + 0 => x`, `0 + x => x`
- Subtractive Identity: `x - 0 => x`, `x - x => 0`
- Multiplicative Identity: `x * 1 => x`, `1 * x => x`
- Multiplicative Zero: `x * 0 => 0`, `0 * x => 0`
- Division Identities: `x / 1 => x`, `0 / x => 0` (for `x != 0`)
- Exponentiation / Power: `x ^ 0 => 1`
- Bitwise Identities: `x & 0 => 0`, `x & x => x`, `x | 0 => x`, `x | x => x`

### 3.4 Dead Code Elimination (DCE)
- The user can declare which variables are **live** at the exit of the basic block (variables whose values are consumed after the block terminates).
- The optimizer executes a mark-sweep graph traversal starting from:
  1. Nodes labeled with live-out variables.
  2. Side-effecting operations (such as array store instructions `a[i] = x`).
- All reachable ancestor nodes are marked active. Unreachable interior nodes are flagged as dead, visually highlighted as pruned in the graph, and omitted during target code emission.

### 3.5 Code Generation from the DAG
The compiler reconstructs optimized Three-Address Code by executing a topological sort over the active nodes:
- For each interior node, a primary variable is selected from its label set to receive the operator computation.
- Secondary variables bound to the same node are emitted as simple register copies (`var2 = primary`).
- Constant and copy statements are emitted only when bound to live output variables.

---

## 4. Supported Three-Address Code Syntax

The lexer and parser support standard compiler Three-Address Code instructions:

| Instruction Type | Concrete Syntax Examples |
| :--- | :--- |
| Binary Arithmetic | `a = b + c`, `d = x * y`, `t1 = p / q`, `m = k % 4` |
| Binary Bitwise & Relational | `r = a & b`, `flag = x == y`, `c = m < n` |
| Unary Operations | `x = -y`, `b = not flag`, `z = ~mask` |
| Literal Assignment | `x = 10`, `y = 3.14`, `flag = true` |
| Copy Assignment | `a = b` |
| Array Read (Load) | `t1 = a[i]`, `val = arr[4]` |
| Array Write (Store) | `a[i] = val` |
| Branching & Labels | `label L1:`, `goto L2`, `if x > 0 goto L1`, `return res` |
| Comments | Single-line comments using `#` or `//` |

---

## 5. System Architecture

The project is structured into two decoupled tiers:

```
DAG Based local optimization/
├── backend/
│   ├── compiler/
│   │   ├── __init__.py        # Package exports
│   │   ├── ir.py              # Intermediate representation, TAC parser, basic block partitioner
│   │   ├── dag.py             # DAG node/edge structures, value numbering, step-by-step tracing
│   │   ├── optimizer.py       # Liveness analysis, dead code elimination, topological code emission
│   │   └── presets.py         # Standard textbook benchmark suites
│   ├── main.py                # FastAPI REST endpoints with CORS middleware
│   ├── test_compiler.py       # Comprehensive unit test suite
│   └── requirements.txt       # Python package dependencies
│
└── frontend/
    ├── index.html             # Application entry point with web font imports
    ├── package.json           # Dependencies: React 19, @xyflow/react, dagre, lucide-react
    ├── tsconfig.json          # TypeScript compiler configuration
    ├── vite.config.ts         # Vite bundler configuration and reverse proxy
    └── src/
        ├── App.tsx            # Main application coordinator
        ├── index.css          # Design system tokens and layout rules
        ├── types.ts           # Shared TypeScript interfaces
        ├── api.ts             # Backend communication client
        └── components/
            ├── Header.tsx          # Top bar, preset selector, and action buttons
            ├── CodeEditor.tsx      # Line-numbered editor, passes switches, live-variable selector
            ├── DagCanvas.tsx       # React Flow canvas with Dagre hierarchical layout
            ├── CustomDagNode.tsx   # Custom SVG/HTML node cards with status indicators
            ├── StepScrubber.tsx    # Playback controls for step-by-step construction
            ├── ComparisonPanel.tsx # Side-by-side diff, reduction metrics, decision timeline
            └── TheoryModal.tsx     # Reference guide detailing compiler optimization theory
```

### Visual Design System
The user interface implements a distinctive, high-contrast palette:
- **Mint / Soft Turquoise (`#8AD6D1`)**: Active node highlights, glow rings, variable leaves, and code tags.
- **Deep Teal (`#359FA0`)**: Primary action controls, DAG dependency flow edges, and active toggle states.
- **Warm Cream (`#FFF0C5`)**: Constant nodes, variable label tags, metric values, and prominent headings.
- **Coral Sunset (`#FF8C52`)**: Brand gradient badge, reduction percentage indicators, and CSE shared node highlights.
- **Deep Ocean Slate (`#0A171D`)**: Primary canvas, panels, and code editor surfaces.

---

## 6. Predefined Textbook Benchmarks

DAGOpt includes seven curated benchmark cases accessible via the dropdown menu:

1. **Classic Common Subexpression Elimination:** Demonstrates `b + c` reuse across variable assignments `a` and `d`.
2. **Dragon Book Array Address Calculation:** Demonstrates eliminating duplicate `4 * i` byte-offset calculations in consecutive array lookups.
3. **Reassignment and Variable Shadowing:** Verifies correct label management when variables `b` and `d` are reassigned inside the block.
4. **Constant Folding and Propagation Chain:** Demonstrates compiling `x = 10`, `y = 20`, `z = x + y`, `w = z * 2` into a folded constant `60`.
5. **Algebraic Simplification Identities:** Evaluates identities such as `x + 0`, `y * 1`, `z * 0`, and `w - w`.
6. **Dead Code Elimination:** Identifies instructions producing values unread by any live variable and prunes them from the DAG.
7. **Complex Symmetrical Tree:** Compiles `(a + b) * (c + d)` computed twice into a shared symmetrical graph.

---

## 7. Installation and Execution Guide

### 7.1 Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher with npm

### 7.2 Backend Setup
Open a terminal in the root repository directory:

```bash
# Install backend dependencies
python -m pip install fastapi uvicorn pydantic

# Launch the FastAPI backend server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend server runs at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

### 7.3 Frontend Setup
Open a second terminal in the repository directory:

```bash
# Navigate to the frontend directory
cd frontend

# Install frontend packages
npm install

# Start the Vite development server
npm run dev
```

The web application runs at `http://localhost:5173`.

### 7.4 Running Automated Compiler Tests
To verify the compiler algorithms independently of the browser interface:

```bash
python -m backend.test_compiler
```

All unit tests will execute and output test status for parsing, value numbering, constant folding, commutative matching, algebraic reduction, and dead code pruning.

---

## 8. API Specification

### `POST /api/optimize`
Executes local DAG optimization on the provided code block.

**Request Payload:**
```json
{
  "code": "a = b + c\nd = b + c\ne = a * d",
  "block_id": "B1",
  "enable_cse": true,
  "enable_constant_folding": true,
  "enable_constant_propagation": true,
  "enable_algebraic_simplification": true,
  "enable_dead_code_elimination": true,
  "custom_live_vars": ["e"]
}
```

**Response Attributes:**
- `basic_blocks`: List of detected basic blocks with start and end line bounds.
- `original_instructions`: Formatted three-address statements before optimization.
- `optimized_instructions`: Formatted three-address statements generated from the DAG.
- `dag_nodes`: Node definitions including operator type, children IDs, variable labels, and constant values.
- `dag_edges`: Edge connections representing value flow.
- `step_traces`: Ordered array of snapshots capturing DAG construction state at every instruction.
- `stats`: Numerical metrics including instructions saved, reduction percentage, CSE hits, constant folds, and pruned nodes.

### `GET /api/presets`
Returns the catalog of predefined compiler benchmark cases.

### `POST /api/validate`
Validates intermediate representation syntax and partitions the input into basic blocks.

---

## 9. Verification Results

The test suite validates the following compiler invariants:
- **Parser Robustness:** Correctly ignores comments and identifies binary operations, unary operations, array indexing, and constant loads.
- **CSE Deduplication:** Confirms identical subexpressions map to identical internal node IDs.
- **Commutative Equivalence:** Confirms `a = b + c` and `d = c + b` resolve to a single node.
- **Constant Folding Chain:** Verifies transitive folding over dependent operations.
- **Algebraic Identity Verification:** Verifies zero multiplication and self-subtraction collapse to constant zero nodes.
- **Liveness Pruning:** Confirms variables excluded from the live-out set produce no instructions in the emitted code.
