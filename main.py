import asyncio

import typer

try:
    from .orchestrator import execute_workflow
    from .storage import (
        get_runs_for_workflow,
        init_db,
        list_runs,
    )
except ImportError:
    # Handle standalone execution
    from orchestrator import execute_workflow
    from storage import (
        get_runs_for_workflow,
        init_db,
        list_runs,
    )


app = typer.Typer(help="CLI for running multi-agent workflows.")


@app.callback()
def default(yaml_path: str = typer.Option(None, "--yaml", help="Run a workflow YAML immediately and exit")) -> None:
    """Optionally run a workflow via --yaml; otherwise use subcommands."""
    if yaml_path:
        init_db()
        asyncio.run(execute_workflow(yaml_path))


@app.command()
def run(yaml_path: str) -> None:
    """Run a workflow from a YAML file path."""
    init_db()
    asyncio.run(execute_workflow(yaml_path))


@app.command("list-runs")
def list_runs_cmd(limit: int = typer.Option(20, help="Number of rows to list")) -> None:
    """List recent agent runs."""
    init_db()
    rows = list_runs(limit=limit)
    for rid, wf, agent, status, cost in rows:
        print(f"#{rid} | {wf} | {agent} | {status} | cost={'{:.4f}'.format(cost)}")


@app.command()
def show_runs(
    workflow: str = typer.Option(..., "--workflow", "-w", help="Workflow name"),
    limit: int = typer.Option(10, help="Limit rows"),
) -> None:
    """Show runs for a specific workflow."""
    init_db()
    rows = get_runs_for_workflow(workflow, limit=limit)
    for rid, wf, agent, status, cost, output in rows:
        preview = (output or "").strip().replace("\n", " ")
        if len(preview) > 160:
            preview = preview[:160] + "…"
        print(f"#{rid} | {wf} | {agent} | {status} | cost={'{:.4f}'.format(cost)}")
        if preview:
            print(f"   ↳ {preview}")


@app.command("list-workflow-runs")
def list_workflow_runs(workflow: str = typer.Option(None, "--workflow", "-w", help="Filter by workflow")) -> None:
    """List workflow run groups (from workflow_runs table)."""
    try:
        from .storage import _conn  # local import to avoid exposing in API
    except ImportError:
        from storage import _conn

    init_db()
    with _conn() as conn:
        if workflow:
            cur = conn.execute(
                "SELECT id, workflow, started_at, finished_at FROM workflow_runs WHERE workflow = ? ORDER BY id DESC",
                (workflow,),
            )
        else:
            cur = conn.execute(
                "SELECT id, workflow, started_at, finished_at FROM workflow_runs ORDER BY id DESC",
            )
        for rid, wf, started, finished in cur.fetchall():
            print(f"run_id={rid} | {wf} | started={started} | finished={finished}")


@app.command("show-run")
def show_run(run_id: int) -> None:
    """Show all agent runs for a workflow run id."""
    try:
        from .storage import _conn  # local import to avoid exposing in API
    except ImportError:
        from storage import _conn

    init_db()
    with _conn() as conn:
        cur = conn.execute(
            "SELECT id, workflow, agent, status, cost, output FROM runs WHERE workflow_run_id = ? ORDER BY id",
            (run_id,),
        )
        rows = cur.fetchall()
        if not rows:
            print("No runs found for run_id", run_id)
            return
        for rid, wf, agent, status, cost, output in rows:
            preview = (output or "").strip().replace("\n", " ")
            if len(preview) > 160:
                preview = preview[:160] + "…"
            print(f"#{rid} | {wf} | {agent} | {status} | cost={'{:.4f}'.format(cost)}")
            if preview:
                print(f"   ↳ {preview}")


def main() -> None:  # for python -m agentops
    app()


if __name__ == "__main__":
    main()


