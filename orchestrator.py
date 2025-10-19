from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Set

from yaml import safe_load
from rich.console import Console

try:
    from .models import AgentRun, WorkflowSpec
    from .runner import run_agent
    from .storage import save_run, create_workflow_run, finalize_workflow_run
except ImportError:
    from models import AgentRun, WorkflowSpec
    from runner import run_agent
    from storage import save_run, create_workflow_run, finalize_workflow_run


async def execute_workflow(yaml_path: str) -> None:
    spec = WorkflowSpec(**safe_load(Path(yaml_path).read_text()))
    console = Console()
    console.print(f"🚀 Starting workflow: [bold]{spec.name}[/bold]")

    agent_name_to_result: Dict[str, AgentRun] = {}
    workflow_run_id = create_workflow_run(spec.name)
    remaining: Dict[str, object] = {a.name: a for a in spec.agents}
    deps: Dict[str, object] = {a.name: a.depends_on for a in spec.agents}

    while remaining:
        ready_batch: List[str] = []
        for name, dep in deps.items():
            if name not in remaining:
                continue
            if not dep:
                ready_batch.append(name)
            else:
                # Support string or list (AND semantics)
                if isinstance(dep, str):
                    dep_res = agent_name_to_result.get(dep)
                    if dep_res and dep_res.status == "success":
                        ready_batch.append(name)
                else:
                    # list of deps
                    all_ok = True
                    for d in dep:
                        res = agent_name_to_result.get(d)
                        if not res or res.status != "success":
                            all_ok = False
                            break
                    if all_ok:
                        ready_batch.append(name)

        if not ready_batch:
            # Deadlock or all remaining depend on failed agents
            for name in list(remaining.keys()):
                print(f"⏭ Skipping {name}, dependency failed or missing.")
                remaining.pop(name, None)
            break

        async def run_one(name: str) -> None:
            agent = remaining[name]
            console.print(f"▶ Running agent: {name}")
            upstream_output = None
            dep = deps.get(name)
            if dep:
                if isinstance(dep, str):
                    dep_res = agent_name_to_result.get(dep)
                    upstream_output = dep_res.output if dep_res and dep_res.output else None
                else:
                    # concatenate outputs from all deps
                    parts: List[str] = []
                    for d in dep:
                        dr = agent_name_to_result.get(d)
                        if dr and dr.output:
                            parts.append(f"[{d}]\n{dr.output}")
                    upstream_output = "\n\n".join(parts) if parts else None
            
            result = await run_agent(agent, context=upstream_output)  # type: ignore[arg-type]
            agent_name_to_result[name] = result
            save_run(spec.name, result, workflow_run_id=workflow_run_id)
            if result.status == "success":
                preview = (result.output or "").strip().replace("\n", " ")
                if len(preview) > 200:
                    preview = preview[:200] + "…"
                console.print(f"✅ [green]{name}[/green] succeeded (${'{:.4f}'.format(result.cost)})")
                if preview:
                    console.print(f"   ↳ {preview}")
            else:
                console.print(f"❌ [red]{name}[/red] failed after {result.retries} retries: {result.error}")

        # run batch in parallel
        await asyncio.gather(*(run_one(n) for n in ready_batch))

        # remove completed from remaining
        for n in ready_batch:
            remaining.pop(n, None)

    if agent_name_to_result:
        console.print("\n— Results —")
        for name, res in agent_name_to_result.items():
            console.print(f"{name}: {res.status}, cost={'{:.4f}'.format(res.cost)}")

    finalize_workflow_run(workflow_run_id)
    console.print("\n✅ Workflow complete.")


