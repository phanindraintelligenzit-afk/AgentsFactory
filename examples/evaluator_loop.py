"""Example: Evaluator-Optimizer loop pattern.

Demonstrates iterative refinement where a generator produces output,
an evaluator scores it, and the loop continues until quality threshold
or max iterations.
"""

import asyncio
from agentkit.agents.builder import AgentBuilder
from agentkit.core.context import ContextManager
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
from agentkit.orchestrator.engine import Orchestrator
from agentkit.observability.tracer import PipelineTracer


async def main():
    topology = TopologyConfig(
        name="refinement_loop",
        topology_type=TopologyType.EVALUATOR_OPTIMIZER,
        agents=[
            AgentConfig(
                agent_id="generator",
                role="writer",
                model="openrouter/owl-alpha",
            ),
            AgentConfig(
                agent_id="evaluator",
                role="evaluator",
                model="openrouter/owl-alpha",
            ),
        ],
        evaluator_agent_id="evaluator",
        max_iterations=3,
        score_threshold=0.85,
    )

    builder = AgentBuilder()
    context_manager = ContextManager()
    agents = builder.build_from_configs(topology.agents, context_manager)

    tracer = PipelineTracer()
    orchestrator = Orchestrator(config=topology, agents=agents, tracer=tracer)

    print("🔄 Running evaluator-optimizer loop...")
    state = await orchestrator.execute(
        input_text="Write a concise explanation of circuit breakers in distributed systems.",
    )

    print(f"\n📊 Results:")
    print(f"   Status: {state.status}")
    print(f"   Iterations: {state.metadata.get('iterations', 'N/A')}")
    print(f"   Best score: {state.metadata.get('best_score', 'N/A')}")
    print(f"   Total agents called: {len(state.agent_results)}")


if __name__ == "__main__":
    asyncio.run(main())
