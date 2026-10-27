"""
Comprehensive unit test suite for the DAGOpt compiler engine.
Run with: python -m pytest backend/test_compiler.py
"""

from backend.compiler.ir import TACParser, InstructionType
from backend.compiler.dag import DAGBuilder
from backend.compiler.optimizer import DAGOptimizer
from backend.compiler.presets import PRESETS


def test_parser_basic():
    code = """
    // comments should be ignored
    a = b + c
    d = 42
    e = -f
    arr[i] = x
    y = arr[i]
    """
    insts = TACParser.parse_program(code)
    assert len(insts) == 5
    assert insts[0].inst_type == InstructionType.BINARY_OP
    assert insts[0].dst == "a" and insts[0].src1 == "b" and insts[0].op == "+" and insts[0].src2 == "c"
    assert insts[1].inst_type == InstructionType.CONSTANT
    assert insts[1].dst == "d" and insts[1].const_val == 42
    assert insts[2].inst_type == InstructionType.UNARY_OP
    assert insts[2].dst == "e" and insts[2].src1 == "f"
    assert insts[3].inst_type == InstructionType.ARRAY_STORE
    assert insts[4].inst_type == InstructionType.ARRAY_LOAD


def test_classic_cse():
    code = """
    a = b + c
    d = b + c
    e = a * d
    """
    insts = TACParser.parse_program(code)
    blocks = TACParser.partition_basic_blocks(insts)
    assert len(blocks) == 1

    optimizer = DAGOptimizer(enable_cse=True)
    res = optimizer.optimize_basic_block(blocks[0], code)

    # In CSE, d = b + c should reuse the node created for a = b + c
    assert res.stats["cse_hits"] == 1
    # Check that 'd' was mapped to the same node as 'a'
    assert res.var_table["a"] == res.var_table["d"]
    # Check step traces recorded CSE_HIT
    cse_traces = [t for t in res.step_traces if t["action_type"] == "CSE_HIT"]
    assert len(cse_traces) == 1
    assert "Common Subexpression" in cse_traces[0]["description"]


def test_commutative_cse():
    code = """
    a = b + c
    d = c + b
    """
    insts = TACParser.parse_program(code)
    blocks = TACParser.partition_basic_blocks(insts)

    optimizer = DAGOptimizer(enable_cse=True)
    res = optimizer.optimize_basic_block(blocks[0], code)

    assert res.stats["cse_hits"] == 1
    assert res.var_table["a"] == res.var_table["d"]


def test_constant_folding():
    code = """
    x = 10
    y = 20
    z = x + y
    w = z * 2
    """
    insts = TACParser.parse_program(code)
    blocks = TACParser.partition_basic_blocks(insts)

    optimizer = DAGOptimizer(enable_constant_folding=True, enable_constant_propagation=True)
    res = optimizer.optimize_basic_block(blocks[0], code)

    assert res.stats["constant_folds"] >= 2
    # Verify node containing 'w' has folded const_value = 60
    w_node_id = res.var_table["w"]
    w_node = next(n for n in res.dag_nodes if n["id"] == w_node_id)
    assert w_node["const_value"] == 60


def test_algebraic_simplification():
    code = """
    a = x + 0
    b = y * 1
    c = z * 0
    d = w - w
    """
    insts = TACParser.parse_program(code)
    blocks = TACParser.partition_basic_blocks(insts)

    optimizer = DAGOptimizer(enable_algebraic_simplification=True)
    res = optimizer.optimize_basic_block(blocks[0], code)

    assert res.stats["algebraic_simplifications"] == 4
    # c should be mapped to const 0
    c_node_id = res.var_table["c"]
    c_node = next(n for n in res.dag_nodes if n["id"] == c_node_id)
    assert c_node["const_value"] == 0

    # d should also be mapped to const 0
    d_node_id = res.var_table["d"]
    d_node = next(n for n in res.dag_nodes if n["id"] == d_node_id)
    assert d_node["const_value"] == 0


def test_dead_code_elimination():
    code = """
    t1 = a + b
    dead_val = c * d
    unused = dead_val - 5
    result = t1 * 2
    """
    insts = TACParser.parse_program(code)
    blocks = TACParser.partition_basic_blocks(insts)

    optimizer = DAGOptimizer(
        enable_dead_code_elimination=True,
        custom_live_vars=["result"]
    )
    res = optimizer.optimize_basic_block(blocks[0], code)

    assert res.stats["dead_nodes_eliminated"] > 0
    # dead_val and unused should not be in the generated code
    assert "dead_val" not in res.optimized_code
    assert "unused" not in res.optimized_code
def test_all_presets_compile():
    for preset in PRESETS:
        insts = TACParser.parse_program(preset["code"])
        blocks = TACParser.partition_basic_blocks(insts)
        assert len(blocks) >= 1
        optimizer = DAGOptimizer()
        res = optimizer.optimize_basic_block(blocks[0], preset["code"])
        assert len(res.dag_nodes) > 0
        assert len(res.step_traces) > 0
        assert res.optimized_code is not None


if __name__ == "__main__":

    print("Running DAGOpt Compiler Engine Unit Tests...")
    test_parser_basic()
    print("[PASS] test_parser_basic passed")
    test_classic_cse()
    print("[PASS] test_classic_cse passed")
    test_commutative_cse()
    print("[PASS] test_commutative_cse passed")
    test_constant_folding()
    print("[PASS] test_constant_folding passed")
    test_algebraic_simplification()
    print("[PASS] test_algebraic_simplification passed")
    test_dead_code_elimination()
    print("[PASS] test_dead_code_elimination passed")
    test_all_presets_compile()
    print("[PASS] test_all_presets_compile passed (all presets valid)")
    print("\nALL COMPILER UNIT TESTS PASSED!")


