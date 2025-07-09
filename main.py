# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

"""
This sample demonstrates two LLM agents:
Local Insider: Suggests a madrid itinerary from their diaries in a vectorstorre with prices in Euros
Travel Expert: Adds the total cost of the itinerary and converts to NZD using an API

The user inputs their budget in NZD and the Local Insider suggests an itinerary.
The agents 'chat' in a loop until the Travel says the itinerary is within budget.
"""

class ItineraryApprovalTerminationStrategy(TerminationStrategy):
    """Ends the chat when the Travel Expert approves the itinerary."""

    async def should_agent_terminate(self, agent, history):
        return "itinerary approved" in history[-1].content.lower()


LOCAL_INSIDER_NAME = "LocalInsider"
LOCAL_INSIDER_INSTRUCTIONS = """
You are a Local Insider in Madrid. 
Your job is to suggest an itinerary for the user for a whole day in Madrid including times and prices in Eurosfor each activity.
Your goal is to get the approval of the Travel Expert. 
Always begin with the most expensive activities in the itenerary and then gradually swap out one high cost activity for a lower cost one each time the travel expert declines until the Travel Expert approves.
Do not ask any questions, and do not convert to NZD. Just suggest the itinerary.
"""

TRAVEL_EXPERT_NAME = "TravelExpert"
TRAVEL_EXPERT_INSTRUCTIONS = """
You are a travel expert. 
You recieve the itinerary from the local insider and calculate how many much it will cost in total in Euros. You will then convert the total cost to NZD.
The budget is 50 NZD per day.
If the itinerary is under 50 NZD, sayexactly the words itinerary approved, not intinerary is approved. 
If the itinerary is over 50 NZD, say it's not approved and ask the travel expert to suggest a cheaper itinerary.
Do not ask any questions. And do not mention what the budget is.
"""


async def main():
    model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-4o")

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create the Chef agent
        local_insider_definition = await client.agents.create_agent(
            model=model_deployment_name,
            name=LOCAL_INSIDER_NAME,
            instructions=LOCAL_INSIDER_INSTRUCTIONS,
        )

        local_insider_agent = AzureAIAgent(
            client=client,
            definition=local_insider_definition,
        )

        # 2. Create the Nutrition Coach agent
        travel_expert_definition = await client.agents.create_agent(
            model=model_deployment_name,
            name=TRAVEL_EXPERT_NAME,
            instructions=TRAVEL_EXPERT_INSTRUCTIONS,
        )

        travel_expert_agent = AzureAIAgent(
            client=client,
            definition=travel_expert_definition,
        )

        # 3. Put them in a group chat with custom termination
        chat = AgentGroupChat(
            agents=[local_insider_agent, travel_expert_agent],
            termination_strategy=ItineraryApprovalTerminationStrategy(
                agents=[travel_expert_agent], maximum_iterations=10
            ),
        )

        try:
            print("Welcome to the Bespoke Travel Agency!")
            print("Type 'exit' or 'quit' to end the chat.\n")
            user_input = input("Where would you like to go? ").strip()

            while user_input.lower() not in ("exit", "quit"):
                await chat.add_chat_message(message=user_input)
                print(f"# {AuthorRole.USER}: '{user_input}'")

                async for content in chat.invoke():
                    print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

                user_input = input("\nYour next request: ").strip()

        finally:
            await chat.reset()
            await client.agents.delete_agent(local_insider_definition.id)
            await client.agents.delete_agent(travel_expert_definition.id)


if __name__ == "__main__":
    asyncio.run(main())
