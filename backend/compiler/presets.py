"""
Predefined Compiler Optimization Examples (Textbook & Benchmark Cases).
"""

from typing import Dict, List


PRESETS: List[Dict[str, str]] = [
    {
        "id": "classic_cse",
        "title": "Classic Common Subexpression Elimination",
        "category": "CSE",
        "description": "Textbook example where 'b + c' is computed twice. The DAG optimizer detects the identical expression and shares the node.",
        "code": """a = b + c
d = b + c
e = a * d""",
    },
    {
        "id": "array_indexing",
        "title": "Dragon Book Array Address Calculation",
        "category": "CSE & Arrays",
        "description": "Classic 4*i byte offset calculation for array indexing. The second 4*i computation is eliminated via DAG value numbering.",
        "code": """t1 = 4 * i
t2 = a[t1]
t3 = 4 * i
t4 = b[t3]
t5 = t2 + t4""",
    },
    {
        "id": "reassignment_shadowing",
        "title": "Reassignment and Variable Shadowing",
        "category": "DAG Label Management",
        "description": "Demonstrates variable reassignment where variables 'b' and 'd' are updated. Note how subsequent expressions use new definitions.",
        "code": """a = b + c
b = a - d
c = b + c
d = a - d""",
    },
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
        "id": "algebraic_identities",
        "title": "Algebraic Simplification Identities",
        "category": "Algebraic",
        "description": "Applies mathematical identities: x + 0 => x, y * 1 => y, z * 0 => 0, w - w => 0.",
        "code": """a = x + 0
b = y * 1
c = z * 0
d = w - w
result = a + b""",
    },
    {
        "id": "dead_code_elimination",
        "title": "Dead Code Elimination",
        "category": "Dead Code",
        "description": "Calculates 'dead_val' and 'unused' which are never used in computing 'result'. DCE prunes these redundant operations from the DAG.",
        "code": """t1 = a + b
dead_val = c * d
t2 = t1 + 10
unused = dead_val - 5
result = t2 * 2""",
    },
    {
        "id": "multi_expression_dag",
        "title": "Complex Symmetrical Tree",
        "category": "Combined",
        "description": "Computes (a + b) * (c + d) twice. The DAG combines both symmetric subtrees into a compact shared graph.",
        "code": """t1 = a + b
t2 = c + d
t3 = t1 * t2
t4 = a + b
t5 = c + d
t6 = t4 * t5
res = t3 + t6""",
    },
]
