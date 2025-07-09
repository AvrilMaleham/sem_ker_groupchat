from semantic_kernel.agents.strategies import TerminationStrategy


class ItineraryApprovalTerminationStrategy(TerminationStrategy):
    """Ends the chat when the Travel Expert approves the itinerary."""

    async def should_agent_terminate(self, agent, history):
        return "itinerary approved" in history[-1].content.lower() 