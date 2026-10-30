"""
Predefined Compiler Optimization Examples (Textbook & Benchmark Cases).
Organized cleanly across compiler design categories.
"""

from typing import Dict, List


PRESETS: List[Dict[str, str]] = [
    # =========================================================================
    # 1. Common Subexpression Elimination (CSE)
    # =========================================================================
    {
        "id": "classic_cse",
        "title": "Classic CSE (Aho & Ullman)",
        "category": "CSE",
        "description": "Textbook example where 'b + c' is computed twice. The DAG optimizer detects the identical expression and shares the node.",
        "code": """a = b + c
d = b + c
e = a * d""",
    },
    {
        "id": "commutative_cse",
        "title": "Commutative Value Numbering",
        "category": "CSE",
        "description": "Demonstrates commutativity in DAG construction: 'b + c' and 'c + b' are recognized as mathematically identical and merged into a single node.",
        "code": """a = b + c
d = c + b
e = a * d""",
    },
    {
        "id": "nested_cse",
        "title": "Multi-Level Nested Subexpressions",
        "category": "CSE",
        "description": "Both first-level (a + b) and second-level ((a + b) + c) subexpressions are duplicated and shared across multiple instructions.",
        "code": """t1 = a + b
t2 = t1 + c
t3 = a + b
t4 = t3 + c
ans = t2 * t4""",
    },
    {
        "id": "multi_expression_dag",
        "title": "Complex Symmetrical Tree",
        "category": "CSE",
        "description": "Computes (a + b) * (c + d) twice. The DAG combines both symmetric subtrees into a compact shared graph.",
        "code": """t1 = a + b
t2 = c + d
t3 = t1 * t2
t4 = a + b
t5 = c + d
t6 = t4 * t5
res = t3 + t6""",
    },

    # =========================================================================
    # 2. Array Addressing & Memory Operations
    # =========================================================================
    {
        "id": "array_indexing",
        "title": "Dragon Book Array Address Calculation",
        "category": "Array & Memory",
        "description": "Classic 4*i byte offset calculation for array indexing (e.g. a[i] + b[i]). The second 4*i computation is eliminated via DAG value numbering.",
        "code": """t1 = 4 * i
t2 = a[t1]
t3 = 4 * i
t4 = b[t3]
t5 = t2 + t4""",
    },
    {
        "id": "matrix_addressing",
        "title": "2D Matrix Row-Major Indexing",
        "category": "Array & Memory",
        "description": "Simulates 2D matrix element access row*cols + col. Identical offset computations are reused across matrix operations.",
        "code": """offset1 = row * 8
idx1 = offset1 + col
val1 = A[idx1]
offset2 = row * 8
idx2 = offset2 + col
val2 = B[idx2]
result = val1 + val2""",
    },
    {
        "id": "array_store_safety",
        "title": "Array Store Invalidation (Side Effect Safety)",
        "category": "Array & Memory",
        "description": "Demonstrates memory safety: writing to a[i] updates the array state so subsequent reads of a[i] create a new node rather than falsely reusing stale data.",
        "code": """t1 = a[i]
a[i] = new_val
t2 = a[i]
result = t1 + t2""",
    },

    # =========================================================================
    # 3. Variable Reassignment & Shadowing
    # =========================================================================
    {
        "id": "reassignment_shadowing",
        "title": "Variable Reassignment & Shadowing",
        "category": "Label Management",
        "description": "Demonstrates variable reassignment where variables 'b' and 'd' are updated. Note how subsequent expressions use new definitions.",
        "code": """a = b + c
b = a - d
c = b + c
d = a - d""",
    },
    {
        "id": "accumulator_loop_body",
        "title": "In-Place Accumulator Pattern",
        "category": "Label Management",
        "description": "Models a straight-line block where variable 'x' is incremented and scaled in-place. Shows dynamic label detachment and reassignment.",
        "code": """x = x + 1
y = x + 1
x = x * 2
ans = x + y""",
    },

    # =========================================================================
    # 4. Constant Folding & Propagation
    # =========================================================================
    {
        "id": "const_folding_propagation",
        "title": "Constant Folding & Propagation Chain",
        "category": "Constant Folding",
        "description": "Propagates known constants (10, 20) and folds 10 + 20 into 30, then 30 * 2 into 60 at compile-time.",
        "code": """x = 10
y = 20
z = x + y
w = z * 2
ans = w + a""",
    },
    {
        "id": "mixed_constant_arithmetic",
        "title": "Buffer & Header Allocation Math",
        "category": "Constant Folding",
        "description": "Simulates compiler calculating fixed header and buffer sizes. All static dimensions fold into compile-time constants before adding variable payload.",
        "code": """header_size = 64
payload_align = 8
padded_header = header_size + payload_align
buffer_capacity = padded_header * 4
total_allocated = buffer_capacity + user_data""",
    },

    # =========================================================================
    # 5. Algebraic Identities & Simplification
    # =========================================================================
    {
        "id": "algebraic_identities",
        "title": "Arithmetic Simplification Identities",
        "category": "Algebraic Identities",
        "description": "Applies mathematical identities: x + 0 => x, y * 1 => y, z * 0 => 0, w - w => 0, k / 1 => k.",
        "code": """a = x + 0
b = y * 1
c = z * 0
d = w - w
e = k / 1
result = a + b""",
    },
    {
        "id": "bitwise_identities",
        "title": "Bitwise & Logical Identities",
        "category": "Algebraic Identities",
        "description": "Applies bitwise identities: x & 0 => 0, x | 0 => x, x & x => x, x | x => x.",
        "code": """a = mask & 0
b = flags | 0
c = status & status
d = val | val
result = b + c""",
    },
    {
        "id": "zero_cascade",
        "title": "Zero Multiplication Cascade",
        "category": "Algebraic Identities",
        "description": "Multiplying complex subexpressions by 0 immediately collapses the entire subtree into a single constant node 0.",
        "code": """t1 = a * b
t2 = c + d
t3 = t1 * 0
t4 = 0 * t2
ans = t3 + t4""",
    },

    # =========================================================================
    # 6. Dead Code Elimination (DCE)
    # =========================================================================
    {
        "id": "dead_code_elimination",
        "title": "Dead Intermediate Computations",
        "category": "Dead Code Elimination",
        "description": "Calculates 'dead_val' and 'unused' which are never used in computing 'result'. DCE prunes these redundant operations from the DAG.",
        "code": """t1 = a + b
dead_val = c * d
t2 = t1 + 10
unused = dead_val - 5
result = t2 * 2""",
    },
    {
        "id": "dead_subtree",
        "title": "Entire Dead Subtree Pruning",
        "category": "Dead Code Elimination",
        "description": "An entire multi-node branch (t1, t2, t3) is constructed but never consumed by the live-out variable 'res'. The entire branch is pruned.",
        "code": """t1 = x * y
t2 = t1 + z
t3 = t2 / 2
useful = p + q
res = useful * 5""",
    },

    # =========================================================================
    # 7. Control Flow & Multi-Block Partitioning
    # =========================================================================
    {
        "id": "multi_block_flow",
        "title": "Control Flow Basic Block Partitioning",
        "category": "Control Flow & Blocks",
        "description": "Contains conditional jumps and labels. DAGOpt automatically detects leaders and partitions instructions into distinct basic blocks B1, B2, B3.",
        "code": """t1 = a + b
t2 = c + d
if t1 > 10 goto L1
t3 = a + b
goto L2
label L1:
t4 = c + d
label L2:
res = t1 + t2""",
    },
]
