"""Simple example: Sequential pipeline with 3 agents.

This demonstrates the basic usage of AgentsFactory:
1. Define agent configs
2. Create an orchestrator
3. Execute a pipeline
"""

import asyncio
from agentkit.agents.builder import AgentBuilder
from agentkit.core.context import ContextManager
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
from agentkit.orchestrator.engine import Orchestrator
from agentkit.observability.tracer import PipelineTracer


async def main():
    # 1. Define the pipeline topology
    topology = TopologyConfig(
        name="research_pipeline",
        topology_type=TopologyType.SEQUENTIAL,
        agents=[
            AgentConfig(
                agent_id="researcher",
                role="researcher",
                model="openrouter/owl-alpha",
            ),
            AgentConfig(
                agent_id="analyzer",
                role="analyzer",
                model="openrouter/owl-alpha",
            ),
            AgentConfig(
                agent_id="writer",
                role="writer",
                model="openrouter/owl-alpha",
            ),
        ],
    )

    # 2. Build agents
    builder = AgentBuilder()
    context_manager = ContextManager()
    agents = builder.build_from_configs(topology.agents, context_manager)

    # 3. Create orchestrator
    tracer = PipelineTracer()
    orchestrator = Orchestrator(
        config=topology,
        agents=agents,
        tracer=tracer,
    )

    # 4. Execute
    print("🚀 Executing pipeline...")
    state = await orchestrator.execute(
        input_text="What are the latest trends in AI agent orchestration?",
        constraints=["Focus on technical depth", "Cite specific frameworks"],
    )

    # 5. Inspect results
    print(f"\n📊 Pipeline Results:")
    print(f"   Status: {state.status}")
    print(f"   Trace ID: {state.trace_id}")
    print(f"   Total tokens: {state.total_tokens}")
    print(f"   Total cost: ${state.total_cost_usd:.6f}")
    print(f"   Total latency: {state.total_latency_ms:.0f}ms")
    print(f"\n🤖 Agent Results:")
    for agent_id, result in state.agent_results.items():
        print(f"   {agent_id}: {result.status.value} (confidence: {result.confidence:.2f})")
        if result.summary:
            print(f"     Summary: {result.summary[:100]}...")

    # 6. Get trace
    summary = tracer.get_summary(state)
    print(f"\n📋 Trace Summary:")
    print(f"   Spans: {summary['total_spans']}")
    print(f"   Agents: {len(summary['agents'])}")


if __name__ == "__main__":
    asyncio.run(main())
