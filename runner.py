import asyncio
from typing import Optional

try:
    from .models import AgentRun, AgentSpec
    from .utils import call_llm, estimate_cost
except ImportError:
    from models import AgentRun, AgentSpec
    from utils import call_llm, estimate_cost


async def run_agent(agent: AgentSpec, context: Optional[str] = None) -> AgentRun:
    max_retries = 2
    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            prompt = agent.task
            if context:
                prompt = f"{agent.task}\n\nContext from dependency:\n{context}"
            output = await call_llm(agent.model, prompt)
            cost = estimate_cost(output)
            return AgentRun(
                name=agent.name,
                status="success",
                cost=cost,
                output=output,
                error=None,
                retries=attempt,
            )
        except Exception as exc:  # noqa: BLE001 - surface any exception from SDK/network
            last_error = exc
            print(f"⚠️ Agent {agent.name} failed (attempt {attempt + 1}): {exc}")
            await asyncio.sleep(2)

    return AgentRun(
        name=agent.name,
        status="failed",
        cost=0.0,
        output=None,
        error=str(last_error) if last_error else "unknown error",
        retries=max_retries,
    )


