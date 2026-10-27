"""
Optimizer: Dead Code Elimination, Variable Liveness, and Optimized Three-Address Code Generation from DAG.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .ir import BasicBlock, Instruction, is_numeric_or_literal
from .dag import DAGBuilder, DagNode, DagEdge


@dataclass
class OptimizationResult:
    original_code: str
    original_instructions: List[Instruction]
    optimized_instructions: List[str]
    optimized_code: str
    dag_nodes: List[Dict[str, Any]]
    dag_edges: List[Dict[str, Any]]
    step_traces: List[Dict[str, Any]]
    var_table: Dict[str, str]
    live_out: List[str]
    stats: Dict[str, Any]
    explanations: List[str]


class DAGOptimizer:
    def __init__(
        self,
        enable_cse: bool = True,
        enable_constant_folding: bool = True,
        enable_constant_propagation: bool = True,
        enable_algebraic_simplification: bool = True,
        enable_dead_code_elimination: bool = True,
        custom_live_vars: Optional[List[str]] = None,
    ):
        self.enable_cse = enable_cse
        self.enable_constant_folding = enable_constant_folding
        self.enable_constant_propagation = enable_constant_propagation
        self.enable_algebraic_simplification = enable_algebraic_simplification
        self.enable_dead_code_elimination = enable_dead_code_elimination
        self.custom_live_vars = set(custom_live_vars) if custom_live_vars is not None else None

    def _determine_live_out(
        self, block: BasicBlock, builder: DAGBuilder
    ) -> Set[str]:
        """
        Determines the set of variables that are considered LIVE at the exit of this basic block.
        If user supplied a custom list, use that.
        Otherwise, by default:
        - Non-temporary user variables (variables not matching 't[0-9]+' or '_' prefix)
        - If all variables are temporaries, all assigned variables in the block.
        """
        if self.custom_live_vars is not None:
            return set(self.custom_live_vars)

        all_assigned = block.defined_vars()
        if not all_assigned:
            # Fallback to variables currently mapped in builder
            all_assigned = set(builder.var_to_node.keys())

        # Filter out purely intermediate temporaries (like t1, t2, _t1) unless that's all there is
        user_vars = {
            v for v in all_assigned
            if not (v.startswith("_") or (len(v) >= 2 and v[0].lower() == "t" and v[1:].isdigit()))
        }

        # If user only used temporaries (e.g. t1 = a + b, t2 = t1 * 2), keep the final assigned variables
        if not user_vars:
            return all_assigned

        return user_vars

    def _apply_dead_code_elimination(
        self, builder: DAGBuilder, live_out: Set[str]
    ) -> Tuple[int, List[str]]:
        """
        Marks dead nodes and edges in the DAG.
        Returns (number_of_dead_nodes, list_of_explanations).
        """
        explanations = []
        dead_count = 0

        # Mark-sweep from live variables & effectful nodes
        live_node_ids: Set[str] = set()
        queue = deque()

        # Step 1: Find root live nodes
        for nid, node in builder.nodes.items():
            # Array store instructions are effectful and must stay live
            if node.kind == "ARRAY_OP" and node.op == "[]=":
                live_node_ids.add(nid)
                queue.append(nid)
                continue

            # Nodes that have at least one live-out variable attached
            live_labels = [lbl for lbl in node.labels if lbl in live_out]
            if live_labels:
                live_node_ids.add(nid)
                queue.append(nid)

        # Step 2: Traverse dependencies (children of live nodes must be kept alive)
        while queue:
            curr_id = queue.popleft()
            curr_node = builder.nodes.get(curr_id)
            if not curr_node:
                continue
            for child_id in curr_node.children:
                if child_id not in live_node_ids and child_id in builder.nodes:
                    live_node_ids.add(child_id)
                    queue.append(child_id)

        # Step 3: Flag dead nodes and edges
        for nid, node in builder.nodes.items():
            if nid not in live_node_ids:
                node.is_dead = True
                dead_count += 1
                explanations.append(
                    f"Dead Code Elimination: Node {nid} ({node.op}, labels: {node.labels}) has no live outputs and is pruned."
                )

        for edge in builder.edges:
            if edge.source not in live_node_ids or edge.target not in live_node_ids:
                edge.is_dead = True

        return dead_count, explanations

    def _generate_code_from_dag(
        self,
        builder: DAGBuilder,
        live_out: Set[str],
        original_insts: List[Instruction],
    ) -> List[str]:
        """
        Reconstructs minimal, correct Three-Address Code from the DAG.
        Follows standard topological order: children before parents.
        """
        nodes = builder.nodes
        generated_code: List[str] = []

        # Find nodes to evaluate
        # Filter dead nodes if DCE enabled
        active_nids = [
            nid for nid, n in nodes.items()
            if not (self.enable_dead_code_elimination and n.is_dead)
        ]

        # In-degree calculation for topological sort
        # A node depends on its children. So children must be evaluated before parents!
        # Thus in DAG evaluation order: child -> parent.
        # Graph edges point Parent -> Child. Reverse is Child -> Parent.
        parents_of: Dict[str, Set[str]] = {nid: set() for nid in active_nids}
        children_of: Dict[str, Set[str]] = {nid: set() for nid in active_nids}

        for nid in active_nids:
            node = nodes[nid]
            for cid in node.children:
                if cid in parents_of:
                    parents_of[cid].add(nid)
                    children_of[nid].add(cid)

        # Topological sort (Kahn's algorithm: start with nodes that have 0 children to compute)
        # Leaves have 0 children
        in_degree = {nid: len(children_of[nid]) for nid in active_nids}
        ready = deque([nid for nid in active_nids if in_degree[nid] == 0])

        topo_order: List[str] = []
        while ready:
            curr = ready.popleft()
            topo_order.append(curr)
            for pid in parents_of[curr]:
                in_degree[pid] -= 1
                if in_degree[pid] == 0:
                    ready.append(pid)

        # Any cycle fallback (should not happen in DAG, but safeguard)
        if len(topo_order) < len(active_nids):
            for nid in active_nids:
                if nid not in topo_order:
                    topo_order.append(nid)

        # Map each active node to the symbol/variable that holds its computed value at runtime
        node_value_repr: Dict[str, str] = {}
        temp_counter = 1

        # Track emitted assignments to avoid duplicates
        emitted_vars: Set[str] = set()

        for nid in topo_order:
            node = nodes[nid]

            # 1. Leaf constant: can directly be represented by its literal
            if node.kind == "LEAF_CONST":
                node_value_repr[nid] = str(node.op)
                # If a live variable is bound to this constant, emit assignment: var = const
                for lbl in node.labels:
                    if (not self.enable_dead_code_elimination or lbl in live_out) and lbl not in emitted_vars:
                        generated_code.append(f"{lbl} = {node.op}")
                        emitted_vars.add(lbl)
                        node_value_repr[nid] = lbl
                continue

            # 2. Leaf variable: represented by its original variable name
            if node.kind == "LEAF_VAR":
                node_value_repr[nid] = node.op
                # If another variable was copied from it (e.g. b was initial, a = b)
                for lbl in node.labels:
                    if lbl != node.op:
                        if (not self.enable_dead_code_elimination or lbl in live_out) and lbl not in emitted_vars:
                            generated_code.append(f"{lbl} = {node.op}")
                            emitted_vars.add(lbl)
                continue

            # 3. Array store: a[i] = x
            if node.kind == "ARRAY_OP" and node.op == "[]=":
                arr_repr = node_value_repr.get(node.children[0], node.children[0])
                idx_repr = node_value_repr.get(node.children[1], node.children[1])
                val_repr = node_value_repr.get(node.children[2], node.children[2])
                generated_code.append(f"{arr_repr}[{idx_repr}] = {val_repr}")
                continue

            # 4. Interior Operator / Array Load:
            # Pick a primary variable to receive the computation
            # Prefer live-out variables in node.labels, then other labels, else create a temp
            chosen_primary = None
            for lbl in node.labels:
                if not self.enable_dead_code_elimination or lbl in live_out:
                    chosen_primary = lbl
                    break

            if not chosen_primary and node.labels:
                chosen_primary = node.labels[0]

            if not chosen_primary:
                chosen_primary = f"t{temp_counter}"
                temp_counter += 1

            node_value_repr[nid] = chosen_primary

            # Format the RHS expression
            if node.kind == "ARRAY_OP" and node.op == "[]":
                arr_repr = node_value_repr.get(node.children[0], node.children[0])
                idx_repr = node_value_repr.get(node.children[1], node.children[1])
                generated_code.append(f"{chosen_primary} = {arr_repr}[{idx_repr}]")
            elif len(node.children) == 1:
                # Unary op
                child_repr = node_value_repr.get(node.children[0], node.children[0])
                if node.op in {"not", "!"}:
                    generated_code.append(f"{chosen_primary} = not {child_repr}")
                else:
                    generated_code.append(f"{chosen_primary} = {node.op}{child_repr}")
            elif len(node.children) == 2:
                # Binary op
                left_repr = node_value_repr.get(node.children[0], node.children[0])
                right_repr = node_value_repr.get(node.children[1], node.children[1])
                generated_code.append(f"{chosen_primary} = {left_repr} {node.op} {right_repr}")

            emitted_vars.add(chosen_primary)

            # Copy to any other live variables sharing this computed value
            for lbl in node.labels:
                if lbl != chosen_primary and (not self.enable_dead_code_elimination or lbl in live_out):
                    if lbl not in emitted_vars:
                        generated_code.append(f"{lbl} = {chosen_primary}")
                        emitted_vars.add(lbl)

        return generated_code

    def optimize_basic_block(
        self, block: BasicBlock, original_code_str: str
    ) -> OptimizationResult:
        """
        Runs the full DAG-based local optimization pipeline on a basic block.
        """
        # Step 1: Construct DAG with Value Numbering, CSE, Constant Folding, Algebraic Identities
        builder = DAGBuilder(
            enable_cse=self.enable_cse,
            enable_constant_folding=self.enable_constant_folding,
            enable_constant_propagation=self.enable_constant_propagation,
            enable_algebraic_simplification=self.enable_algebraic_simplification,
        )

        for idx, inst in enumerate(block.instructions):
            builder.process_instruction(idx, inst)

        # Step 2: Determine Live-Out Variables
        live_out = self._determine_live_out(block, builder)

        # Step 3: Dead Code Elimination (if enabled)
        dead_count = 0
        dce_explanations = []
        if self.enable_dead_code_elimination:
            dead_count, dce_explanations = self._apply_dead_code_elimination(builder, live_out)

        # Step 4: Generate Optimized 3-Address Code
        optimized_lines = self._generate_code_from_dag(
            builder=builder,
            live_out=live_out,
            original_insts=block.instructions,
        )

        # Step 5: Gather Metrics and Explanations
        orig_count = len(block.instructions)
        opt_count = len(optimized_lines)
        diff_count = max(0, orig_count - opt_count)
        reduction_pct = round((diff_count / orig_count * 100), 1) if orig_count > 0 else 0.0

        explanations: List[str] = []
        if builder.cse_count > 0:
            explanations.append(
                f"Common Subexpression Elimination: Eliminated {builder.cse_count} redundant computation(s) by reusing DAG nodes."
            )
        if builder.constant_fold_count > 0:
            explanations.append(
                f"Constant Folding: Computed {builder.constant_fold_count} operation(s) at compile-time."
            )
        if builder.algebraic_simplification_count > 0:
            explanations.append(
                f"Algebraic Simplification: Simplified {builder.algebraic_simplification_count} expression(s) using arithmetic identities (e.g. x+0, x*1, x-x)."
            )
        if dead_count > 0:
            explanations.extend(dce_explanations)

        if not explanations:
            explanations.append("Code is already minimal for the selected passes; no redundant operations found.")

        stats = {
            "original_instruction_count": orig_count,
            "optimized_instruction_count": opt_count,
            "instructions_saved": diff_count,
            "reduction_percentage": reduction_pct,
            "cse_hits": builder.cse_count,
            "constant_folds": builder.constant_fold_count,
            "algebraic_simplifications": builder.algebraic_simplification_count,
            "dead_nodes_eliminated": dead_count,
            "total_dag_nodes": len(builder.nodes),
            "total_dag_edges": len(builder.edges),
        }

        dag_nodes_dict = [n.to_dict() for n in builder.nodes.values()]
        dag_edges_dict = [e.to_dict() for e in builder.edges]
        step_traces_dict = [t.to_dict() for t in builder.traces]

        return OptimizationResult(
            original_code=original_code_str,
            original_instructions=block.instructions,
            optimized_instructions=optimized_lines,
            optimized_code="\n".join(optimized_lines),
            dag_nodes=dag_nodes_dict,
            dag_edges=dag_edges_dict,
            step_traces=step_traces_dict,
            var_table=builder.var_to_node,
            live_out=sorted(list(live_out)),
            stats=stats,
            explanations=explanations,
        )
