"""
FastAPI application for DAGOpt: Interactive DAG-Based Local Code Optimizer.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.compiler.ir import TACParser, BasicBlock
from backend.compiler.optimizer import DAGOptimizer
from backend.compiler.presets import PRESETS

app = FastAPI(
    title="DAGOpt API",
    description="Backend API for DAG-Based Local Code Optimization and Visualization",
    version="1.0.0",
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizationRequest(BaseModel):
    code: str
    block_id: Optional[str] = None
    enable_cse: bool = True
    enable_constant_folding: bool = True
    enable_constant_propagation: bool = True
    enable_algebraic_simplification: bool = True
    enable_dead_code_elimination: bool = True
    custom_live_vars: Optional[List[str]] = None


class ValidationRequest(BaseModel):
    code: str


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "DAGOpt Optimizer Engine"}


@app.get("/api/presets")
def get_presets():
    return {"presets": PRESETS}


@app.post("/api/validate")
def validate_code(req: ValidationRequest):
    try:
        insts = TACParser.parse_program(req.code)
        blocks = TACParser.partition_basic_blocks(insts)
        return {
            "valid": True,
            "instruction_count": len(insts),
            "blocks": [
                {
                    "id": b.id,
                    "name": b.name,
                    "start_line": b.start_line,
                    "end_line": b.end_line,
                    "instruction_count": len(b.instructions),
                }
                for b in blocks
            ],
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


@app.post("/api/optimize")
def optimize_code(req: OptimizationRequest):
    code = req.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    try:
        instructions = TACParser.parse_program(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing error: {str(e)}")

    if not instructions:
        raise HTTPException(status_code=400, detail="No valid 3-Address instructions found.")

    blocks = TACParser.partition_basic_blocks(instructions)
    if not blocks:
        raise HTTPException(status_code=400, detail="Failed to partition basic blocks.")

    # Select target basic block
    target_block: BasicBlock = blocks[0]
    if req.block_id:
        for b in blocks:
            if b.id == req.block_id:
                target_block = b
                break

    optimizer = DAGOptimizer(
        enable_cse=req.enable_cse,
        enable_constant_folding=req.enable_constant_folding,
        enable_constant_propagation=req.enable_constant_propagation,
        enable_algebraic_simplification=req.enable_algebraic_simplification,
        enable_dead_code_elimination=req.enable_dead_code_elimination,
        custom_live_vars=req.custom_live_vars,
    )

    block_code_str = "\n".join(inst.to_tac_string() for inst in target_block.instructions)
    result = optimizer.optimize_basic_block(target_block, block_code_str)

    # All variables defined or used in the basic block (for user to easily select live variables)
    available_vars = sorted(list(target_block.defined_vars().union(target_block.used_vars())))

    return {
        "success": True,
        "basic_blocks": [
            {
                "id": b.id,
                "name": b.name,
                "start_line": b.start_line,
                "end_line": b.end_line,
                "instruction_count": len(b.instructions),
            }
            for b in blocks
        ],
        "active_block": target_block.id,
        "original_code": block_code_str,
        "original_instructions": [inst.to_tac_string() for inst in target_block.instructions],
        "optimized_code": result.optimized_code,
        "optimized_instructions": result.optimized_instructions,
        "dag_nodes": result.dag_nodes,
        "dag_edges": result.dag_edges,
        "step_traces": result.step_traces,
        "var_table": result.var_table,
        "live_out": result.live_out,
        "available_vars": available_vars,
        "stats": result.stats,
        "explanations": result.explanations,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
