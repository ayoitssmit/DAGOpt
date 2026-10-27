"""
Intermediate Representation (IR) and Three-Address Code (TAC) Parser.
Supports basic block partitioning and instruction analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import List, Optional, Set, Tuple, Union


class OpKind(str, Enum):
    # Binary Arithmetic & Bitwise
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    FLOORDIV = "//"
    MOD = "%"
    POW = "^"
    AND = "&"
    OR = "|"
    XOR = "^"
    SHL = "<<"
    SHR = ">>"
    
    # Comparisons
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    
    # Unary
    NEG = "neg"
    NOT = "not"
    BITNOT = "~"


class InstructionType(str, Enum):
    BINARY_OP = "BINARY_OP"
    UNARY_OP = "UNARY_OP"
    COPY = "COPY"
    CONSTANT = "CONSTANT"
    ARRAY_LOAD = "ARRAY_LOAD"
    ARRAY_STORE = "ARRAY_STORE"
    LABEL = "LABEL"
    GOTO = "GOTO"
    IF_GOTO = "IF_GOTO"
    RETURN = "RETURN"
    COMMENT = "COMMENT"


COMMUTATIVE_OPS = {
    OpKind.ADD.value, "+",
    OpKind.MUL.value, "*",
    OpKind.AND.value, "&",
    OpKind.OR.value, "|",
    OpKind.EQ.value, "==",
    OpKind.NE.value, "!="
}


@dataclass
class Instruction:
    line_number: int
    raw_text: str
    inst_type: InstructionType
    dst: Optional[str] = None
    src1: Optional[str] = None
    src2: Optional[str] = None
    op: Optional[str] = None
    const_val: Optional[Union[int, float, str, bool]] = None
    label: Optional[str] = None
    target_label: Optional[str] = None
    relop: Optional[str] = None

    def defined_vars(self) -> Set[str]:
        if self.inst_type in {
            InstructionType.BINARY_OP,
            InstructionType.UNARY_OP,
            InstructionType.COPY,
            InstructionType.CONSTANT,
            InstructionType.ARRAY_LOAD,
        } and self.dst:
            return {self.dst}
        return set()

    def used_vars(self) -> Set[str]:
        used = set()
        if self.src1 and not is_numeric_or_literal(self.src1):
            used.add(self.src1)
        if self.src2 and not is_numeric_or_literal(self.src2):
            used.add(self.src2)
        if self.inst_type == InstructionType.ARRAY_STORE:
            if self.dst:
                used.add(self.dst)  # array name
            if self.src1 and not is_numeric_or_literal(self.src1):
                used.add(self.src1)  # index
            if self.src2 and not is_numeric_or_literal(self.src2):
                used.add(self.src2)  # value
        elif self.inst_type == InstructionType.ARRAY_LOAD:
            if self.src1:
                used.add(self.src1)  # array name
            if self.src2 and not is_numeric_or_literal(self.src2):
                used.add(self.src2)  # index
        return used

    def to_tac_string(self) -> str:
        if self.inst_type == InstructionType.BINARY_OP:
            return f"{self.dst} = {self.src1} {self.op} {self.src2}"
        elif self.inst_type == InstructionType.UNARY_OP:
            if self.op in {"not", "!"}:
                return f"{self.dst} = not {self.src1}"
            return f"{self.dst} = {self.op}{self.src1}"
        elif self.inst_type == InstructionType.COPY:
            return f"{self.dst} = {self.src1}"
        elif self.inst_type == InstructionType.CONSTANT:
            return f"{self.dst} = {self.const_val}"
        elif self.inst_type == InstructionType.ARRAY_LOAD:
            return f"{self.dst} = {self.src1}[{self.src2}]"
        elif self.inst_type == InstructionType.ARRAY_STORE:
            return f"{self.dst}[{self.src1}] = {self.src2}"
        elif self.inst_type == InstructionType.LABEL:
            return f"{self.label}:"
        elif self.inst_type == InstructionType.GOTO:
            return f"goto {self.target_label}"
        elif self.inst_type == InstructionType.IF_GOTO:
            if self.relop and self.src2:
                return f"if {self.src1} {self.relop} {self.src2} goto {self.target_label}"
            return f"if {self.src1} goto {self.target_label}"
        elif self.inst_type == InstructionType.RETURN:
            return f"return {self.src1}" if self.src1 else "return"
        return self.raw_text


@dataclass
class BasicBlock:
    id: str
    name: str
    instructions: List[Instruction] = field(default_factory=list)
    start_line: int = 1
    end_line: int = 1
    live_in: Set[str] = field(default_factory=set)
    live_out: Set[str] = field(default_factory=set)

    def is_straight_line(self) -> bool:
        """Checks if the block consists solely of straight-line assignments without jumps."""
        return all(
            inst.inst_type in {
                InstructionType.BINARY_OP,
                InstructionType.UNARY_OP,
                InstructionType.COPY,
                InstructionType.CONSTANT,
                InstructionType.ARRAY_LOAD,
                InstructionType.ARRAY_STORE,
                InstructionType.LABEL,
            }
            for inst in self.instructions
        )

    def defined_vars(self) -> Set[str]:
        vars_set = set()
        for inst in self.instructions:
            vars_set.update(inst.defined_vars())
        return vars_set

    def used_vars(self) -> Set[str]:
        vars_set = set()
        for inst in self.instructions:
            vars_set.update(inst.used_vars())
        return vars_set


def is_numeric_or_literal(token: str) -> bool:
    token = token.strip()
    if token.lower() in {"true", "false"}:
        return True
    try:
        int(token)
        return True
    except ValueError:
        pass
    try:
        float(token)
        return True
    except ValueError:
        pass
    return False


def parse_literal(token: str) -> Union[int, float, bool, str]:
    token = token.strip()
    if token.lower() == "true":
        return True
    if token.lower() == "false":
        return False
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token


class TACParser:
    """
    Parses a string of Three-Address Code instructions.
    Gracefully tolerates variations like missing semicolons, spaces, and comments.
    """

    BINARY_REGEX = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z0-9_.]+)\s*(\+|\-|\*|//|/|%|\^|&|\||<<|>>|==|!=|<=|>=|<|>)\s*([A-Za-z0-9_.]+)$"
    )
    UNARY_REGEX = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-|~|!|not\s+)([A-Za-z0-9_.]+)$"
    )
    COPY_OR_CONST_REGEX = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z0-9_.]+)$"
    )
    ARRAY_LOAD_REGEX = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\[([A-Za-z0-9_.]+)\]$"
    )
    ARRAY_STORE_REGEX = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\[([A-Za-z0-9_.]+)\]\s*=\s*([A-Za-z0-9_.]+)$"
    )
    LABEL_REGEX = re.compile(
        r"^(?:label\s+)?([A-Za-z_][A-Za-z0-9_]*):$"
    )
    GOTO_REGEX = re.compile(
        r"^goto\s+([A-Za-z_][A-Za-z0-9_]*)$"
    )
    IF_GOTO_RELOP_REGEX = re.compile(
        r"^if\s+([A-Za-z0-9_.]+)\s*(==|!=|<=|>=|<|>)\s*([A-Za-z0-9_.]+)\s+goto\s+([A-Za-z_][A-Za-z0-9_]*)$"
    )
    IF_GOTO_SIMPLE_REGEX = re.compile(
        r"^if\s+([A-Za-z0-9_.]+)\s+goto\s+([A-Za-z_][A-Za-z0-9_]*)$"
    )
    RETURN_REGEX = re.compile(
        r"^return(?:\s+([A-Za-z0-9_.]+))?$"
    )

    @classmethod
    def parse_line(cls, line: str, line_no: int) -> Optional[Instruction]:
        clean = line.strip()
        # Remove comments
        clean = re.sub(r"(#|//).*$", "", clean).strip()
        # Remove trailing semicolon if any
        if clean.endswith(";"):
            clean = clean[:-1].strip()
        if not clean:
            return None

        # 1. Label
        m = cls.LABEL_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.LABEL,
                label=m.group(1)
            )

        # 2. Goto
        m = cls.GOTO_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.GOTO,
                target_label=m.group(1)
            )

        # 3. If goto with relop
        m = cls.IF_GOTO_RELOP_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.IF_GOTO,
                src1=m.group(1),
                relop=m.group(2),
                src2=m.group(3),
                target_label=m.group(4)
            )

        # 4. If goto simple
        m = cls.IF_GOTO_SIMPLE_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.IF_GOTO,
                src1=m.group(1),
                target_label=m.group(2)
            )

        # 5. Return
        m = cls.RETURN_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.RETURN,
                src1=m.group(1)
            )

        # 6. Array Store: a[i] = x
        m = cls.ARRAY_STORE_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.ARRAY_STORE,
                dst=m.group(1),
                src1=m.group(2),
                src2=m.group(3)
            )

        # 7. Array Load: x = a[i]
        m = cls.ARRAY_LOAD_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.ARRAY_LOAD,
                dst=m.group(1),
                src1=m.group(2),
                src2=m.group(3)
            )

        # 8. Binary Op: x = y op z
        m = cls.BINARY_REGEX.match(clean)
        if m:
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.BINARY_OP,
                dst=m.group(1),
                src1=m.group(2),
                op=m.group(3),
                src2=m.group(4)
            )

        # 9. Unary Op: x = -y or x = not y
        m = cls.UNARY_REGEX.match(clean)
        if m:
            op_sym = m.group(2).strip()
            return Instruction(
                line_number=line_no,
                raw_text=line,
                inst_type=InstructionType.UNARY_OP,
                dst=m.group(1),
                op=op_sym,
                src1=m.group(3)
            )

        # 10. Copy or Constant: x = y or x = 5
        m = cls.COPY_OR_CONST_REGEX.match(clean)
        if m:
            dst = m.group(1)
            rhs = m.group(2)
            if is_numeric_or_literal(rhs):
                return Instruction(
                    line_number=line_no,
                    raw_text=line,
                    inst_type=InstructionType.CONSTANT,
                    dst=dst,
                    const_val=parse_literal(rhs),
                    src1=rhs
                )
            else:
                return Instruction(
                    line_number=line_no,
                    raw_text=line,
                    inst_type=InstructionType.COPY,
                    dst=dst,
                    src1=rhs
                )

        raise ValueError(f"Syntax error at line {line_no}: '{line.strip()}' is not a valid 3-Address instruction.")

    @classmethod
    def parse_program(cls, code: str) -> List[Instruction]:
        instructions = []
        for line_no, line in enumerate(code.splitlines(), start=1):
            inst = cls.parse_line(line, line_no)
            if inst is not None:
                instructions.append(inst)
        return instructions

    @classmethod
    def partition_basic_blocks(cls, instructions: List[Instruction]) -> List[BasicBlock]:
        """
        Partitions instructions into Basic Blocks according to Dragon Book rules:
        1. First instruction is a leader.
        2. Target of any conditional/unconditional jump is a leader.
        3. Instruction immediately following a jump is a leader.
        """
        if not instructions:
            return []

        n = len(instructions)
        is_leader = [False] * n
        is_leader[0] = True

        # Build label -> instruction index map
        label_to_idx = {}
        for idx, inst in enumerate(instructions):
            if inst.inst_type == InstructionType.LABEL and inst.label:
                label_to_idx[inst.label] = idx

        for idx, inst in enumerate(instructions):
            if inst.inst_type in {InstructionType.GOTO, InstructionType.IF_GOTO}:
                # Target of jump is leader
                if inst.target_label and inst.target_label in label_to_idx:
                    is_leader[label_to_idx[inst.target_label]] = True
                # Instruction right after jump is leader
                if idx + 1 < n:
                    is_leader[idx + 1] = True
            elif inst.inst_type == InstructionType.RETURN:
                if idx + 1 < n:
                    is_leader[idx + 1] = True
            elif inst.inst_type == InstructionType.LABEL:
                is_leader[idx] = True

        blocks: List[BasicBlock] = []
        current_block: Optional[BasicBlock] = None
        block_idx = 1

        for idx, inst in enumerate(instructions):
            if is_leader[idx]:
                if current_block and current_block.instructions:
                    current_block.end_line = current_block.instructions[-1].line_number
                    blocks.append(current_block)
                block_name = f"B{block_idx}"
                if inst.inst_type == InstructionType.LABEL and inst.label:
                    block_name = f"B{block_idx} ({inst.label})"
                current_block = BasicBlock(
                    id=f"B{block_idx}",
                    name=block_name,
                    instructions=[],
                    start_line=inst.line_number,
                    end_line=inst.line_number
                )
                block_idx += 1

            if current_block is not None:
                current_block.instructions.append(inst)

        if current_block and current_block.instructions:
            current_block.end_line = current_block.instructions[-1].line_number
            blocks.append(current_block)

        return blocks
