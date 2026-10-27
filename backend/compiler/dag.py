"""
DAG (Directed Acyclic Graph) representation and construction engine for Basic Blocks.
Implements:
- Value numbering & Common Subexpression Elimination (CSE)
- Constant Folding & Constant Propagation
- Algebraic Simplification (identities)
- Variable label management & copy propagation
- Fine-grained step-by-step trace generation for interactive animation
"""

from dataclasses import dataclass, field
import copy
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .ir import (
    Instruction,
    InstructionType,
    COMMUTATIVE_OPS,
    is_numeric_or_literal,
    parse_literal,
)


@dataclass
class DagNode:
    id: str
    kind: str  # "LEAF_VAR", "LEAF_CONST", "INTERIOR_OP", "ARRAY_OP"
    op: str    # variable name, constant representation, or operator symbol (+, *, etc.)
    children: List[str] = field(default_factory=list)  # list of child node IDs
    labels: List[str] = field(default_factory=list)    # variables currently holding this value
    const_value: Optional[Union[int, float, bool, str]] = None
    is_reused: bool = False
    is_folded: bool = False
    is_simplified: bool = False
    is_dead: bool = False
    creation_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "op": self.op,
            "children": list(self.children),
            "labels": list(self.labels),
            "const_value": self.const_value,
            "is_reused": self.is_reused,
            "is_folded": self.is_folded,
            "is_simplified": self.is_simplified,
            "is_dead": self.is_dead,
            "creation_reason": self.creation_reason,
        }


@dataclass
class DagEdge:
    id: str
    source: str  # parent node ID
    target: str  # child node ID
    label: str = ""  # "L", "R", "idx", "val", etc.
    is_dead: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "is_dead": self.is_dead,
        }


@dataclass
class StepTrace:
    step_number: int
    instruction_index: int
    instruction_text: str
    action_type: str  # "INIT", "LEAF_LOOKUP", "CSE_HIT", "CONSTANT_FOLD", "ALGEBRAIC_SIMPLIFY", "NEW_NODE", "COPY", "ARRAY_OP"
    description: str
    active_node_id: Optional[str] = None
    reused_node_id: Optional[str] = None
    folded_node_id: Optional[str] = None
    nodes_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    edges_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    var_table_snapshot: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "instruction_index": self.instruction_index,
            "instruction_text": self.instruction_text,
            "action_type": self.action_type,
            "description": self.description,
            "active_node_id": self.active_node_id,
            "reused_node_id": self.reused_node_id,
            "folded_node_id": self.folded_node_id,
            "nodes_snapshot": self.nodes_snapshot,
            "edges_snapshot": self.edges_snapshot,
            "var_table_snapshot": self.var_table_snapshot,
        }


class DAGBuilder:
    def __init__(
        self,
        enable_cse: bool = True,
        enable_constant_folding: bool = True,
        enable_constant_propagation: bool = True,
        enable_algebraic_simplification: bool = True,
    ):
        self.enable_cse = enable_cse
        self.enable_constant_folding = enable_constant_folding
        self.enable_constant_propagation = enable_constant_propagation
        self.enable_algebraic_simplification = enable_algebraic_simplification

        self.nodes: Dict[str, DagNode] = {}
        self.edges: List[DagEdge] = []
        self.var_to_node: Dict[str, str] = {}  # var_name -> node_id
        self.leaf_var_nodes: Dict[str, str] = {}  # initial var -> node_id
        self.const_nodes: Dict[str, str] = {}  # str(const_val) -> node_id
        self.expr_to_node: Dict[Tuple, str] = {}  # (op, child1_id, [child2_id]) -> node_id
        self.array_states: Dict[str, int] = {}  # array_name -> version counter

        self.node_counter = 1
        self.edge_counter = 1
        self.traces: List[StepTrace] = []
        self.cse_count = 0
        self.constant_fold_count = 0
        self.algebraic_simplification_count = 0

    def _next_node_id(self) -> str:
        nid = f"n{self.node_counter}"
        self.node_counter += 1
        return nid

    def _add_edge(self, parent_id: str, child_id: str, label: str = "") -> DagEdge:
        eid = f"e{self.edge_counter}_{parent_id}_{child_id}"
        self.edge_counter += 1
        edge = DagEdge(id=eid, source=parent_id, target=child_id, label=label)
        self.edges.append(edge)
        return edge

    def _snapshot_nodes(self) -> List[Dict[str, Any]]:
        return [copy.deepcopy(node.to_dict()) for node in self.nodes.values()]

    def _snapshot_edges(self) -> List[Dict[str, Any]]:
        return [copy.deepcopy(edge.to_dict()) for edge in self.edges]

    def _record_trace(
        self,
        inst_idx: int,
        inst_text: str,
        action_type: str,
        description: str,
        active_node_id: Optional[str] = None,
        reused_node_id: Optional[str] = None,
        folded_node_id: Optional[str] = None,
    ):
        trace = StepTrace(
            step_number=len(self.traces) + 1,
            instruction_index=inst_idx,
            instruction_text=inst_text,
            action_type=action_type,
            description=description,
            active_node_id=active_node_id,
            reused_node_id=reused_node_id,
            folded_node_id=folded_node_id,
            nodes_snapshot=self._snapshot_nodes(),
            edges_snapshot=self._snapshot_edges(),
            var_table_snapshot=dict(self.var_to_node),
        )
        self.traces.append(trace)

    def _get_or_create_const_node(self, val: Union[int, float, bool, str]) -> str:
        key = str(val)
        if key in self.const_nodes:
            return self.const_nodes[key]

        nid = self._next_node_id()
        node = DagNode(
            id=nid,
            kind="LEAF_CONST",
            op=str(val),
            children=[],
            labels=[],
            const_value=val,
            creation_reason=f"Constant literal {val}",
        )
        self.nodes[nid] = node
        self.const_nodes[key] = nid
        return nid

    def _get_or_create_leaf_var_node(self, var_name: str) -> str:
        if var_name in self.leaf_var_nodes:
            return self.leaf_var_nodes[var_name]

        nid = self._next_node_id()
        node = DagNode(
            id=nid,
            kind="LEAF_VAR",
            op=var_name,
            children=[],
            labels=[var_name],
            creation_reason=f"Initial value of variable '{var_name}'",
        )
        self.nodes[nid] = node
        self.leaf_var_nodes[var_name] = nid
        self.var_to_node[var_name] = nid
        return nid

    def _resolve_operand(self, token: str) -> str:
        """
        Resolves an operand string into a node ID.
        If it's a numeric literal or constant, returns a const node.
        If it's already in var_to_node, returns the current node computing it.
        Otherwise creates a leaf node for the initial variable value.
        """
        token = token.strip()
        if is_numeric_or_literal(token):
            val = parse_literal(token)
            return self._get_or_create_const_node(val)

        if token in self.var_to_node:
            return self.var_to_node[token]

        # Initial variable access
        return self._get_or_create_leaf_var_node(token)

    def _assign_variable_to_node(self, var_name: str, node_id: str):
        """
        Updates the variable-to-node mapping.
        Removes var_name from old node's label list and adds to new node.
        """
        if var_name in self.var_to_node:
            old_nid = self.var_to_node[var_name]
            if old_nid in self.nodes and var_name in self.nodes[old_nid].labels:
                self.nodes[old_nid].labels.remove(var_name)

        self.var_to_node[var_name] = node_id
        if node_id in self.nodes:
            if var_name not in self.nodes[node_id].labels:
                self.nodes[node_id].labels.append(var_name)

    def _try_eval_constant_binary(
        self, op: str, left_val: Any, right_val: Any
    ) -> Optional[Union[int, float, bool]]:
        try:
            if op == "+":
                return left_val + right_val
            elif op == "-":
                return left_val - right_val
            elif op == "*":
                return left_val * right_val
            elif op == "/":
                return left_val / right_val if right_val != 0 else None
            elif op == "//":
                return left_val // right_val if right_val != 0 else None
            elif op == "%":
                return left_val % right_val if right_val != 0 else None
            elif op == "^":
                return left_val ** right_val if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)) and 0 <= right_val <= 100 else None
            elif op == "&":
                return int(left_val) & int(right_val)
            elif op == "|":
                return int(left_val) | int(right_val)
            elif op == "<<":
                return int(left_val) << int(right_val)
            elif op == ">>":
                return int(left_val) >> int(right_val)
            elif op == "==":
                return left_val == right_val
            elif op == "!=":
                return left_val != right_val
            elif op == "<":
                return left_val < right_val
            elif op == "<=":
                return left_val <= right_val
            elif op == ">":
                return left_val > right_val
            elif op == ">=":
                return left_val >= right_val
        except Exception:
            return None
        return None

    def _try_eval_constant_unary(self, op: str, val: Any) -> Optional[Union[int, float, bool]]:
        try:
            if op in {"-", "neg"}:
                return -val
            elif op in {"not", "!"}:
                return not val
            elif op == "~":
                return ~int(val)
        except Exception:
            return None
        return None

    def _try_algebraic_simplification(
        self, op: str, left_id: str, right_id: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempts algebraic simplification:
        Returns (target_node_id, explanation_str) if simplified, else (None, None).
        """
        left_node = self.nodes.get(left_id)
        right_node = self.nodes.get(right_id)
        if not left_node or not right_node:
            return None, None

        left_is_const = left_node.const_value is not None
        right_is_const = right_node.const_value is not None
        left_c = left_node.const_value
        right_c = right_node.const_value

        # x + 0 = x
        if op == "+" and right_is_const and right_c == 0:
            return left_id, f"Algebraic Identity: x + 0 => {left_node.op}"
        # 0 + x = x
        if op == "+" and left_is_const and left_c == 0:
            return right_id, f"Algebraic Identity: 0 + x => {right_node.op}"

        # x - 0 = x
        if op == "-" and right_is_const and right_c == 0:
            return left_id, f"Algebraic Identity: x - 0 => {left_node.op}"
        # x - x = 0
        if op == "-" and left_id == right_id:
            zero_id = self._get_or_create_const_node(0)
            return zero_id, "Algebraic Identity: x - x => 0"

        # x * 1 = x
        if op == "*" and right_is_const and right_c == 1:
            return left_id, f"Algebraic Identity: x * 1 => {left_node.op}"
        # 1 * x = x
        if op == "*" and left_is_const and left_c == 1:
            return right_id, f"Algebraic Identity: 1 * x => {right_node.op}"

        # x * 0 = 0
        if op == "*" and ((right_is_const and right_c == 0) or (left_is_const and left_c == 0)):
            zero_id = self._get_or_create_const_node(0)
            return zero_id, "Algebraic Identity: x * 0 => 0"

        # x / 1 = x
        if op in {"/", "//"} and right_is_const and right_c == 1:
            return left_id, f"Algebraic Identity: x / 1 => {left_node.op}"
        # 0 / x = 0 (assuming x != 0)
        if op in {"/", "//"} and left_is_const and left_c == 0 and (not right_is_const or right_c != 0):
            zero_id = self._get_or_create_const_node(0)
            return zero_id, "Algebraic Identity: 0 / x => 0"

        # x ^ 0 = 1 (power)
        if op == "^" and right_is_const and right_c == 0:
            one_id = self._get_or_create_const_node(1)
            return one_id, "Algebraic Identity: x ^ 0 => 1"

        # Bitwise identities
        if op == "&" and right_is_const and right_c == 0:
            zero_id = self._get_or_create_const_node(0)
            return zero_id, "Algebraic Identity: x & 0 => 0"
        if op == "&" and left_id == right_id:
            return left_id, f"Algebraic Identity: x & x => {left_node.op}"
        if op == "|" and right_is_const and right_c == 0:
            return left_id, f"Algebraic Identity: x | 0 => {left_node.op}"
        if op == "|" and left_id == right_id:
            return left_id, f"Algebraic Identity: x | x => {left_node.op}"

        return None, None

    def process_instruction(self, inst_idx: int, inst: Instruction):
        """Processes a single instruction and updates the DAG."""
        # 1. Constant Assignment: x = 5
        if inst.inst_type == InstructionType.CONSTANT:
            val = inst.const_val
            cid = self._get_or_create_const_node(val)
            self._assign_variable_to_node(inst.dst, cid)
            self._record_trace(
                inst_idx=inst_idx,
                inst_text=inst.to_tac_string(),
                action_type="CONSTANT",
                description=f"Assigned constant {val} to variable '{inst.dst}'.",
                active_node_id=cid,
            )
            return

        # 2. Copy Assignment: x = y
        if inst.inst_type == InstructionType.COPY:
            src_node_id = self._resolve_operand(inst.src1)
            self._assign_variable_to_node(inst.dst, src_node_id)
            src_node = self.nodes[src_node_id]
            self._record_trace(
                inst_idx=inst_idx,
                inst_text=inst.to_tac_string(),
                action_type="COPY",
                description=f"Copy propagation: mapped '{inst.dst}' to existing Node {src_node_id} (value '{src_node.op}').",
                active_node_id=src_node_id,
            )
            return

        # 3. Unary Operation: x = -y or x = not y
        if inst.inst_type == InstructionType.UNARY_OP:
            src_node_id = self._resolve_operand(inst.src1)
            src_node = self.nodes[src_node_id]

            # Constant folding check
            if (
                self.enable_constant_folding
                and src_node.const_value is not None
            ):
                folded_val = self._try_eval_constant_unary(inst.op, src_node.const_value)
                if folded_val is not None:
                    cid = self._get_or_create_const_node(folded_val)
                    self.nodes[cid].is_folded = True
                    self._assign_variable_to_node(inst.dst, cid)
                    self.constant_fold_count += 1
                    self._record_trace(
                        inst_idx=inst_idx,
                        inst_text=inst.to_tac_string(),
                        action_type="CONSTANT_FOLD",
                        description=f"Constant folded: {inst.op}({src_node.const_value}) = {folded_val}. Variable '{inst.dst}' assigned to Node {cid}.",
                        active_node_id=cid,
                        folded_node_id=cid,
                    )
                    return

            # CSE check for unary op
            key = (inst.op, src_node_id)
            if self.enable_cse and key in self.expr_to_node:
                existing_nid = self.expr_to_node[key]
                self.nodes[existing_nid].is_reused = True
                self._assign_variable_to_node(inst.dst, existing_nid)
                self.cse_count += 1
                self._record_trace(
                    inst_idx=inst_idx,
                    inst_text=inst.to_tac_string(),
                    action_type="CSE_HIT",
                    description=f"Common Subexpression Eliminated: expression '{inst.op}{inst.src1}' was already computed at Node {existing_nid}. Attached label '{inst.dst}'.",
                    active_node_id=existing_nid,
                    reused_node_id=existing_nid,
                )
                return

            # Create new unary node
            nid = self._next_node_id()
            node = DagNode(
                id=nid,
                kind="INTERIOR_OP",
                op=inst.op,
                children=[src_node_id],
                labels=[inst.dst],
                creation_reason=f"Unary operation {inst.op}{inst.src1}",
            )
            self.nodes[nid] = node
            self._add_edge(nid, src_node_id, label="arg")
            self._assign_variable_to_node(inst.dst, nid)
            self.expr_to_node[key] = nid

            self._record_trace(
                inst_idx=inst_idx,
                inst_text=inst.to_tac_string(),
                action_type="NEW_NODE",
                description=f"Created new operator Node {nid} ({inst.op}) with child {src_node_id}. Assigned label '{inst.dst}'.",
                active_node_id=nid,
            )
            return

        # 4. Binary Operation: x = y op z
        if inst.inst_type == InstructionType.BINARY_OP:
            left_id = self._resolve_operand(inst.src1)
            right_id = self._resolve_operand(inst.src2)
            left_node = self.nodes[left_id]
            right_node = self.nodes[right_id]

            # (A) Constant Folding check
            if (
                self.enable_constant_folding
                and left_node.const_value is not None
                and right_node.const_value is not None
            ):
                folded_val = self._try_eval_constant_binary(
                    inst.op, left_node.const_value, right_node.const_value
                )
                if folded_val is not None:
                    cid = self._get_or_create_const_node(folded_val)
                    self.nodes[cid].is_folded = True
                    self._assign_variable_to_node(inst.dst, cid)
                    self.constant_fold_count += 1
                    self._record_trace(
                        inst_idx=inst_idx,
                        inst_text=inst.to_tac_string(),
                        action_type="CONSTANT_FOLD",
                        description=f"Constant folded: {left_node.const_value} {inst.op} {right_node.const_value} = {folded_val}. Variable '{inst.dst}' assigned to Node {cid}.",
                        active_node_id=cid,
                        folded_node_id=cid,
                    )
                    return

            # (B) Algebraic Simplification check
            if self.enable_algebraic_simplification:
                simplified_node_id, reason = self._try_algebraic_simplification(
                    inst.op, left_id, right_id
                )
                if simplified_node_id is not None:
                    self.nodes[simplified_node_id].is_simplified = True
                    self._assign_variable_to_node(inst.dst, simplified_node_id)
                    self.algebraic_simplification_count += 1
                    self._record_trace(
                        inst_idx=inst_idx,
                        inst_text=inst.to_tac_string(),
                        action_type="ALGEBRAIC_SIMPLIFY",
                        description=f"{reason}. Variable '{inst.dst}' mapped directly to Node {simplified_node_id}.",
                        active_node_id=simplified_node_id,
                    )
                    return

            # (C) Common Subexpression Elimination (Value Numbering)
            is_commutative = inst.op in COMMUTATIVE_OPS
            key = (inst.op, left_id, right_id)
            alt_key = (inst.op, right_id, left_id) if is_commutative else None

            existing_nid = None
            if self.enable_cse:
                if key in self.expr_to_node:
                    existing_nid = self.expr_to_node[key]
                elif alt_key and alt_key in self.expr_to_node:
                    existing_nid = self.expr_to_node[alt_key]

            if existing_nid:
                self.nodes[existing_nid].is_reused = True
                self._assign_variable_to_node(inst.dst, existing_nid)
                self.cse_count += 1
                self._record_trace(
                    inst_idx=inst_idx,
                    inst_text=inst.to_tac_string(),
                    action_type="CSE_HIT",
                    description=f"Common Subexpression Eliminated: '{inst.src1} {inst.op} {inst.src2}' was already computed at Node {existing_nid} (labels: {self.nodes[existing_nid].labels}). Reused node and attached label '{inst.dst}'.",
                    active_node_id=existing_nid,
                    reused_node_id=existing_nid,
                )
                return

            # (D) Create New Interior Operator Node
            nid = self._next_node_id()
            node = DagNode(
                id=nid,
                kind="INTERIOR_OP",
                op=inst.op,
                children=[left_id, right_id],
                labels=[inst.dst],
                creation_reason=f"Operation {inst.src1} {inst.op} {inst.src2}",
            )
            self.nodes[nid] = node
            self._add_edge(nid, left_id, label="left")
            self._add_edge(nid, right_id, label="right")
            self._assign_variable_to_node(inst.dst, nid)

            self.expr_to_node[key] = nid
            if alt_key:
                self.expr_to_node[alt_key] = nid

            self._record_trace(
                inst_idx=inst_idx,
                inst_text=inst.to_tac_string(),
                action_type="NEW_NODE",
                description=f"Created new operator Node {nid} [{inst.op}] with children {left_id} ('{left_node.op}') and {right_id} ('{right_node.op}'). Assigned label '{inst.dst}'.",
                active_node_id=nid,
            )
            return

        # 5. Array Load: x = a[i]
        if inst.inst_type == InstructionType.ARRAY_LOAD:
            arr_id = self._resolve_operand(inst.src1)
            idx_id = self._resolve_operand(inst.src2)
            arr_ver = self.array_states.get(inst.src1, 0)
            key = ("[]", arr_id, idx_id, arr_ver)

            if self.enable_cse and key in self.expr_to_node:
                existing_nid = self.expr_to_node[key]
                self.nodes[existing_nid].is_reused = True
                self._assign_variable_to_node(inst.dst, existing_nid)
                self.cse_count += 1
                self._record_trace(
                    inst_idx=inst_idx,
                    inst_text=inst.to_tac_string(),
                    action_type="CSE_HIT",
                    description=f"Redundant array read eliminated: '{inst.src1}[{inst.src2}]' already loaded at Node {existing_nid}. Attached label '{inst.dst}'.",
                    active_node_id=existing_nid,
                    reused_node_id=existing_nid,
                )
                return

            nid = self._next_node_id()
            node = DagNode(
                id=nid,
                kind="ARRAY_OP",
                op="[]",
                children=[arr_id, idx_id],
                labels=[inst.dst],
                creation_reason=f"Array read {inst.src1}[{inst.src2}]",
            )
            self.nodes[nid] = node
            self._add_edge(nid, arr_id, label="array")
            self._add_edge(nid, idx_id, label="index")
            self._assign_variable_to_node(inst.dst, nid)
            self.expr_to_node[key] = nid

            self._record_trace(
                inst_idx=inst_idx,
                inst_text=inst.to_tac_string(),
                action_type="ARRAY_OP",
                description=f"Created array access Node {nid} ({inst.src1}[{inst.src2}]). Assigned label '{inst.dst}'.",
                active_node_id=nid,
            )
            return

        # 6. Array Store: a[i] = x
        if inst.inst_type == InstructionType.ARRAY_STORE:
            arr_id = self._resolve_operand(inst.dst)
            idx_id = self._resolve_operand(inst.src1)
            val_id = self._resolve_operand(inst.src2)

            # Invalidate subsequent loads from array `a`
            self.array_states[inst.dst] = self.array_states.get(inst.dst, 0) + 1

            nid = self._next_node_id()
            node = DagNode(
                id=nid,
                kind="ARRAY_OP",
                op="[]=",
                children=[arr_id, idx_id, val_id],
                labels=[],  # array stores have side effects rather than returning a variable
                creation_reason=f"Array write {inst.dst}[{inst.src1}] = {inst.src2}",
            )
            self.nodes[nid] = node
            self._add_edge(nid, arr_id, label="array")
            self._add_edge(nid, idx_id, label="index")
            self._add_edge(nid, val_id, label="val")

            self._record_trace(
                inst_idx=inst_idx,
                inst_text=inst.to_tac_string(),
                action_type="ARRAY_OP",
                description=f"Created array store Node {nid} ({inst.dst}[{inst.src1}] = {inst.src2}). Array version updated to prevent unsafe load reuse.",
                active_node_id=nid,
            )
            return

        # Fallback for control flow or labels within a block
        self._record_trace(
            inst_idx=inst_idx,
            inst_text=inst.to_tac_string(),
            action_type="PASSTHROUGH",
            description=f"Instruction '{inst.to_tac_string()}' passed through.",
        )
