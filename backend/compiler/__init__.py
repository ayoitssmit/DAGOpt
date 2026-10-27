"""
DAGOpt Compiler Engine Package.
"""

from .ir import TACParser, BasicBlock, Instruction, InstructionType, OpKind
from .dag import DAGBuilder, DagNode, DagEdge, StepTrace
from .optimizer import DAGOptimizer, OptimizationResult
from .presets import PRESETS

__all__ = [
    "TACParser",
    "BasicBlock",
    "Instruction",
    "InstructionType",
    "OpKind",
    "DAGBuilder",
    "DagNode",
    "DagEdge",
    "StepTrace",
    "DAGOptimizer",
    "OptimizationResult",
    "PRESETS",
]
