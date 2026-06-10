"""End-to-end example: Research → Analyze → Write pipeline with real LLMs.

This example:
1. Loads pipeline config from YAML
2. Creates LLM-powered agents
3. Runs the pipeline via the Orchestrator
4. Prints results with full trace

Prerequisites:
- .env file with OPENROUTER_API_KEY set
- uv pip install -e ".[dev]"

Usage:
    uv run python examples/e2e_research.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent
from agentkit.agents.builder import AgentBuilder
from agentkit.config import settings
from agentkit.core.context import ContextManager
from agentkit.llm import LLMClient
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
from agentkit.observability.tracer import PipelineTracer
from agentkit.orchestrator.engine import Orchestrator


def create_llm_agent(agent_id: str, role: str, model: str = "openrouter/owl-alpha"):
    """Create an LLM-powered agent with the right class for its role."""
    config = AgentConfig(
        agent_id=agent_id,
        role=role,
        model=model,
        temperature=0.3 if role != "writer" else 0.5,
        max_tokens=2000,
    )

    role_map = {
        "researcher": ResearcherAgent,
        "analyzer": AnalyzerAgent,
        "writer": WriterAgent,
    }
    agent_class = role_map.get(role, ResearcherAgent)
    return agent_class(config=config)


async def main():
    # Check for API key
    if not settings.openrouter_api_key:
        print("❌ No OPENROUTER_API_KEY found!")
        print("   Create a .env file in the project root with:")
        print("   OPENROUTER_API_KEY=your_key_here")
        print("\n   Get a free key at: https://openrouter.ai/keys")
        return

    print("🚀 AgentsFactory — End-to-End Research Pipeline")
    print("=" * 55)

    # Create agents
    agents = [
        create_llm_agent("researcher", "researcher"),
        create_llm_agent("analyzer", "analyzer"),
        create_llm_agent("writer", "writer"),
    ]

    # Create topology
    topology = TopologyConfig(
        name="research_pipeline",
        topology_type=TopologyType.SEQUENTIAL,
        agents=[a.config for a in agents],
    )

    # Create orchestrator
    tracer = PipelineTracer()
    orchestrator = Orchestrator(
        config=topology,
        agents=agents,
        tracer=tracer,
    )

    # Get input
    topic = "\n📝 Enter a research topic (or press Enter for default): "
    user_input = input(topic).strip()
    if not user_input:
        user_input = "What are the key architectural patterns for building production-grade multi-agent AI systems in 2025?"

    print(f"\n🔍 Researching: {user_input}")
    print("-" * 55)

    # Execute
    state = await orchestrator.execute(
        input_text=user_input,
        constraints=["Be technical and specific", "Include concrete examples"],
    )

    # Results
    print(f"\n📊 Pipeline Complete!")
    print(f"   Status: {state.status}")
    print(f"   Trace ID: {state.trace_id}")
    print(f"   Total tokens: {state.total_tokens}")
    print(f"   Total cost: ${state.total_cost_usd:.6f}")
    print(f"   Total latency: {state.total_latency_ms:.0f}ms")

    print(f"\n🤖 Agent Results:")
    for agent_id, result in state.agent_results.items():
        status_icon = "✅" if result.status.value == "success" else "❌"
        print(f"\n   {status_icon} {agent_id} ({result.status.value})")
        print(f"      Confidence: {result.confidence:.2f}")
        print(f"      Tokens: {result.tokens_used} | Cost: ${result.cost_usd:.6f} | Latency: {result.latency_ms:.0f}ms")
        if result.summary:
            # Print first 3 lines of summary
            lines = result.summary.split("\n")[:3]
            for line in lines:
                print(f"      → {line[:100]}")

    # Final output
    last_agent = list(state.agent_results.values())[-1] if state.agent_results else None
    if last_agent and last_agent.output.get("result"):
        print(f"\n📄 Final Output ({last_agent.agent_id}):")
        print("-" * 55)
        print(last_agent.output["result"][:2000])
        if len(last_agent.output["result"]) > 2000:
            print("\n... (truncated)")

    # Trace summary
    summary = tracer.get_summary(state)
    print(f"\n📋 Trace: {summary['total_spans']} spans recorded")


if __name__ == "__main__":
    asyncio.run(main())
