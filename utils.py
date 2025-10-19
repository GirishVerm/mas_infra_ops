import asyncio
import os
from typing import Optional

from openai import AsyncAzureOpenAI


_client: Optional[AsyncAzureOpenAI] = None


def get_client() -> AsyncAzureOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("AZURE_GPT5_KEY")
        endpoint = os.getenv("AZURE_GPT5_ENDPOINT")
        api_version = os.getenv("AZURE_GPT5_VERSION")
        if not api_key or not endpoint or not api_version:
            raise RuntimeError(
                "Missing Azure OpenAI env vars: AZURE_GPT5_KEY, AZURE_GPT5_ENDPOINT, AZURE_GPT5_VERSION"
            )
        _client = AsyncAzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version=api_version)
    return _client


async def call_llm(model: str, task: str) -> str:
    client = get_client()
    deployment = os.getenv("AZURE_GPT5_DEPLOYMENT") or model
    response = await client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": task}],
        # Some Azure deployments only support default temperature (1)
 
    )
    return response.choices[0].message.content or ""


def estimate_cost(output: str) -> float:
    tokens = len(output.split())
    return tokens * 0.00002


